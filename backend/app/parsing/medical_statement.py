"""진료비 세부산정내역서 파싱 — 항목·합계·환자 정보 추출.

두 입력 경로가 있다:
- PDF(parse_medical_statement): 표 행이 pdfplumber 텍스트 추출 시 한 줄(항목 코드 명칭 금액
  횟수 일수 총액 본인부담금 공단부담금 전액본인부담 비급여)로 이어지는 레이아웃을 정규식으로
  매칭한다. parse_medical_statement_text 자체는 DB·LLM 접근이 없는 순수 함수다.
- 사진(parse_medical_statement_image): 정규식으로 고정할 표 레이아웃이 없어 Vision LLM으로
  구조화 추출한다 — 이쪽은 LLM 호출이 있는 비순수 함수다.

두 경로 모두 같은 모양({"patient_name","hospital_name","period_start","period_end","ward",
"items","summary"})을 반환해 호출측(case_service.py)이 입력 형식과 무관하게 다룰 수 있다.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
from pathlib import Path

from PIL import Image

from app.config import settings
from app.parsing.extractor import extract_pages

_EMPTY_PARSED: dict = {
    "patient_name": None,
    "hospital_name": None,
    "period_start": None,
    "period_end": None,
    "ward": None,
    "items": [],
    "summary": {},
}

# Vision LLM에 보내기 전 리사이즈 상한 — 휴대폰 사진 원본(수천만 화소)을 그대로 보내면
# 토큰 비용·요청 크기가 불필요하게 커진다.
_MAX_IMAGE_DIMENSION = 2000
_VISION_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "parsing" / "medical_statement_vision_prompt.txt"
)

_KNOWN_ITEM_NAMES_BY_CODE = {
    "AA254010": "재진진찰료-의원/보건의료원 내 의과(야간)",
    "MM010": "표층열치료",
    "MM085": "재활저출력레이저치료[1일당]",
}

_ITEM_ROW_RE = re.compile(
    r"^(?P<category>\S+)\s+"
    r"(?P<date>\d{4}\.\d{2}\.\d{2})\s+"
    r"(?P<code>[A-Za-z0-9\-]+)\s+"
    r"(?P<name>.+?)\s+"
    r"(?P<amount>[\d,]+)\s+"
    r"(?P<count>\d+)\s+"
    r"(?P<days>\d+)\s+"
    r"(?P<total>[\d,]+)\s+"
    r"(?P<copay>[\d,]+)\s+"
    r"(?P<insurer>[\d,]+)\s+"
    r"(?P<full_self_pay>[\d,]+)\s+"
    r"(?P<non_covered>[\d,]+)\s*$"
)

_SUMMARY_ROW_RE = re.compile(
    r"^(?P<label>계|끝수처리\s*조정금액|합계)\s+"
    r"(?P<total>-?[\d,]+)\s+"
    r"(?P<copay>-?[\d,]+)\s+"
    r"(?P<insurer>-?[\d,]+)\s+"
    r"(?P<full_self_pay>-?[\d,]+)\s+"
    r"(?P<non_covered>-?[\d,]+)\s*$"
)

_PATIENT_ROW_RE = re.compile(
    r"(?P<patient_id>\S+)\s+(?P<patient_name>\S+)\s+"
    r"(?P<start>\d{4}-\d{2}-\d{2})\s*~\s*(?P<end>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<ward>\S+)\s+(?P<patient_type>\S+)"
)

_HOSPITAL_RE = re.compile(r"요양기관\s*명칭\s+(?P<hospital>\S+)")


def _to_int(text: str) -> int:
    return int(text.replace(",", ""))


def _normalize_item_code(value) -> str | None:
    code = str(value or "").strip().upper()
    return code or None


def _normalize_item_name(code, name) -> str:
    normalized_code = _normalize_item_code(code)
    if normalized_code in _KNOWN_ITEM_NAMES_BY_CODE:
        return _KNOWN_ITEM_NAMES_BY_CODE[normalized_code]
    return str(name or "").strip()


def parse_medical_statement_text(text: str) -> dict:
    """진료비 세부산정내역서 본문 텍스트를 파싱하여 항목·합계·환자 정보를 추출한다.

    반환:
        {
            "patient_name": str | None,
            "hospital_name": str | None,
            "period_start": str | None,  # YYYY-MM-DD
            "period_end": str | None,
            "ward": str | None,  # 병실 원문 (예: "외래")
            "items": [{"category", "code", "name", "count", "days", "total", "non_covered"}, ...],
            "summary": {"total_amount", "patient_paid_amount", "nhis_paid_amount",
                        "full_self_pay_amount", "non_covered_amount"} (없으면 {}),
        }
    """
    items: list[dict] = []
    summary: dict[str, int] = {}
    patient_name = None
    period_start = None
    period_end = None
    ward = None
    hospital_name = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m = _ITEM_ROW_RE.match(line)
        if m:
            code = _normalize_item_code(m["code"])
            items.append(
                {
                    "category": m["category"],
                    "code": code,
                    "name": _normalize_item_name(code, m["name"]),
                    "count": int(m["count"]),
                    "days": int(m["days"]),
                    "total": _to_int(m["total"]),
                    "non_covered": _to_int(m["non_covered"]),
                }
            )
            continue

        m = _SUMMARY_ROW_RE.match(line)
        if m:
            if re.sub(r"\s+", "", m["label"]) == "합계":
                summary = {
                    "total_amount": _to_int(m["total"]),
                    "patient_paid_amount": _to_int(m["copay"]),
                    "nhis_paid_amount": _to_int(m["insurer"]),
                    "full_self_pay_amount": _to_int(m["full_self_pay"]),
                    "non_covered_amount": _to_int(m["non_covered"]),
                }
            continue

        m = _PATIENT_ROW_RE.match(line)
        if m:
            patient_name = m["patient_name"]
            period_start = m["start"]
            period_end = m["end"]
            ward = m["ward"]
            continue

        m = _HOSPITAL_RE.search(line)
        if m:
            hospital_name = m["hospital"]

    return {
        "patient_name": patient_name,
        "hospital_name": hospital_name,
        "period_start": period_start,
        "period_end": period_end,
        "ward": ward,
        "items": items,
        "summary": summary,
    }


def parse_medical_statement(pdf_bytes: bytes) -> dict:
    """진료비 세부산정내역서 PDF 바이트를 파싱한다.

    pdfplumber 의 `extract_text()` 는 일부 레이아웃에서 표 한 행의 셀들을 줄바꿈/공백으로
    분리해버려 정규식 매칭이 깨질 수 있다. 텍스트 기반 파싱이 항목·합계를 못 찾으면
    `extract_tables()` 로 얻은 셀을 한 행씩 공백으로 이어붙여 같은 정규식으로 재시도한다.
    """
    pages = extract_pages(pdf_bytes)
    full_text = "\n".join(p["text"] for p in pages)
    parsed = parse_medical_statement_text(full_text)
    if parsed["items"] and parsed["summary"]:
        return parsed

    table_lines = []
    for page in pages:
        for table in page["tables"]:
            for row in table:
                cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if cells:
                    table_lines.append(" ".join(cells))
    if not table_lines:
        return parsed

    table_parsed = parse_medical_statement_text("\n".join(table_lines))
    return {
        "patient_name": parsed["patient_name"] or table_parsed["patient_name"],
        "hospital_name": parsed["hospital_name"] or table_parsed["hospital_name"],
        "period_start": parsed["period_start"] or table_parsed["period_start"],
        "period_end": parsed["period_end"] or table_parsed["period_end"],
        "ward": parsed["ward"] or table_parsed["ward"],
        "items": parsed["items"] or table_parsed["items"],
        "summary": parsed["summary"] or table_parsed["summary"],
    }


def _load_vision_prompt() -> str:
    if not _VISION_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Vision 프롬프트 파일 누락: {_VISION_PROMPT_PATH}")
    return _VISION_PROMPT_PATH.read_text(encoding="utf-8")


def _resize_for_vision(image_bytes: bytes) -> tuple[bytes, str]:
    """휴대폰 사진 원본을 Vision LLM에 보내기 적당한 크기의 JPEG로 줄인다.

    가로/세로 중 긴 쪽을 `_MAX_IMAGE_DIMENSION` 이하로 맞춰 토큰 비용·요청 크기를 줄인다.
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        if max(img.size) > _MAX_IMAGE_DIMENSION:
            img.thumbnail((_MAX_IMAGE_DIMENSION, _MAX_IMAGE_DIMENSION), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"


def _coerce_int(value) -> int | None:
    """문자열의 쉼표·"원" 단위표시를 정리해 정수로 변환한다.

    None/빈 문자열은 "Vision이 못 읽음"이므로 0으로 둔갑시키지 않고 None(누락)을 그대로
    반환한다 — 호출측에서 None을 0과 구분해 처리해야 한다.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace(",", "").replace("원", "").strip()
        if value == "":
            return None
    return int(value)


def _normalize_vision_result(data: dict) -> dict:
    """Vision LLM JSON 응답을 parse_medical_statement_text 와 동일한 모양으로 정규화한다.

    금액·수량 필드가 누락(None)이면 0으로 채우지 않고 그 항목/summary 자체를 버린다 —
    case_service.py 가 summary 를 그대로 신뢰해 결제금액을 계산하므로, 못 읽은 값이
    0원으로 둔갑해 섞이면 안 된다. non_covered_amount=0 처럼 "키가 있고 실제 값이 0"인
    경우만 0으로 인정한다.
    """
    items = []
    for raw in data.get("items") or []:
        try:
            count = _coerce_int(raw.get("count"))
            days = _coerce_int(raw.get("days"))
            total = _coerce_int(raw.get("total"))
            non_covered = _coerce_int(raw.get("non_covered"))
        except (TypeError, ValueError):
            continue
        if None in (count, days, total, non_covered):
            continue
        code = _normalize_item_code(raw.get("code"))
        items.append(
            {
                "category": str(raw.get("category") or ""),
                "code": code,
                "name": _normalize_item_name(code, raw.get("name")),
                "count": count,
                "days": days,
                "total": total,
                "non_covered": non_covered,
            }
        )

    summary_raw = data.get("summary") or {}
    summary = {}
    if summary_raw:
        try:
            summary_fields = {
                "total_amount": _coerce_int(summary_raw.get("total_amount")),
                "patient_paid_amount": _coerce_int(summary_raw.get("patient_paid_amount")),
                "nhis_paid_amount": _coerce_int(summary_raw.get("nhis_paid_amount")),
                "full_self_pay_amount": _coerce_int(summary_raw.get("full_self_pay_amount")),
                "non_covered_amount": _coerce_int(summary_raw.get("non_covered_amount")),
            }
        except (TypeError, ValueError):
            summary_fields = {}
        if summary_fields and None not in summary_fields.values():
            summary = summary_fields

    return {
        "patient_name": data.get("patient_name"),
        "hospital_name": data.get("hospital_name"),
        "disease_name": data.get("disease_name"),
        "disease_kcd": data.get("disease_kcd"),
        "period_start": data.get("period_start"),
        "period_end": data.get("period_end"),
        "ward": data.get("ward"),
        "items": items,
        "summary": summary,
    }


def parse_medical_statement_image(image_bytes: bytes) -> dict:
    """진료비 세부산정내역서를 촬영한 사진을 Vision LLM(gpt-4o-mini)으로 구조화 추출한다.

    PDF 경로(parse_medical_statement)와 달리 정규식으로 표 레이아웃을 고정할 수 없어
    원문 그대로 신뢰할 근거가 없다 — API 키 미설정·호출 실패·응답 파싱 실패 시 추측하지 않고
    빈 결과(_EMPTY_PARSED)를 반환해 호출측이 "인식 불가" 로 처리하게 한다.
    """
    if os.environ.get("MOCK_LLM") == "True" or not settings.openai_api_key:
        return dict(_EMPTY_PARSED)

    from openai import OpenAI

    try:
        resized_bytes, mime_type = _resize_for_vision(image_bytes)
        encoded = base64.b64encode(resized_bytes).decode("ascii")
        prompt = _load_vision_prompt()

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(response.choices[0].message.content)
        return _normalize_vision_result(data)
    except Exception as e:
        print(f"[MedicalStatement] Vision LLM 추출 실패: {e}")
        return dict(_EMPTY_PARSED)
