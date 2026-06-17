"""약관 파싱 JSON 자동 검수 보조 도구.

목적
  parse_policy.py / parse_rider.py로 만든 riders JSON을 PDF 원문과 다시 대조해
  사람이 먼저 봐야 할 warning/fail 후보를 리포트로 만든다.

중요
  - 이 스크립트가 pass를 냈다고 verified=true가 되는 것은 아니다.
  - verified=true는 사람이 스냅샷/원문을 최종 확인한 뒤에만 부여한다.
  - 기본 실행은 LLM을 쓰지 않는 로컬 검수라 비용 0원이다.
  - --llm 옵션을 켜면 Anthropic API로 원문+JSON 비교 검수를 추가 수행한다.

사용 예
  # 1) 무료 로컬 검수
  python verify_json.py "약관.pdf" "output/약관_전체.json"

  # 2) 로컬 검수에서 warning/fail 난 항목만 AI 검수
  python verify_json.py "약관.pdf" "output/약관_전체.json" --llm

  # 3) 모든 보장을 AI 검수
  python verify_json.py "약관.pdf" "output/약관_전체.json" --llm --llm-scope all

  # 4) 앞에서 5개만 테스트
  python verify_json.py "약관.pdf" "output/약관_전체.json" --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    # scripts/parsing/ → 저장소 루트 .env
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

import pdfplumber

# 같은 폴더에 rider_schema.py가 있으면 스키마 경고를 그대로 활용한다.
try:
    from rider_schema import ParseResult, Rider  # type: ignore
except Exception:  # 스키마가 없어도 최소 검수는 가능하게 둔다.
    ParseResult = None  # type: ignore
    Rider = None  # type: ignore


TRIGGER_TYPES = {"입원", "수술", "진단", "통원", "내원", "골절", "치료", "사망", "후유장해", "기타"}
UNIT_TYPES = {"1일당", "1회당", "일시금", "기타"}
LIMIT_SCOPES = {
    "per_hospitalization",
    "annual",
    "daily",
    "same_cause_window",
    "per_surgery",
    "per_diagnosis",
    "per_visit",
    "lifetime",
    "기타",
}
LIMIT_UNITS = {"days", "count", "krw"}

_PUA = re.compile(r"[\ue000-\uf8ff]")  # 폰트 매핑 실패(Private Use Area) 글자
_SKEL = re.compile(r"[^가-힣0-9]")  # 한글+숫자만 남기는 골격 비교


def skeleton(text: str) -> str:
    return _SKEL.sub("", text or "")


@dataclass
class Issue:
    severity: str  # warning | fail
    field: str
    message: str
    suggested_value: Any = None
    evidence_page: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
        }
        if self.suggested_value is not None:
            out["suggested_value"] = self.suggested_value
        if self.evidence_page is not None:
            out["evidence_page"] = self.evidence_page
        return out


def clean_text(text: str) -> str:
    return (text or "").replace("\x00", " ").replace("\xa0", " ")


def norm_text(text: str) -> str:
    """원문 포함 여부 확인용 정규화. 의미를 바꾸지 않는 표기차만 흡수한다."""
    s = text or ""
    s = (
        s.replace("【", "[")
        .replace("】", "]")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2219", "")
        .replace("\u00b7", "")
        .replace("\u2027", "")
        .replace("ㆍ", "")
        .replace("·", "")
        .replace("∙", "")
        .replace("￾", "")
    )
    s = _PUA.sub("", s)  # 폰트가 못 푼 글자 제거(검수기 page_text 쪽 노이즈)
    s = (
        s.replace("Ⅰ", "I")
        .replace("Ⅱ", "II")
        .replace("Ⅲ", "III")
        .replace("Ⅳ", "IV")
        .replace("Ⅴ", "V")
        .replace("，", ",")
        .replace("．", ".")
        .replace("（", "(")
        .replace("）", ")")
    )
    return re.sub(r"\s+", "", s)


def compact_for_prompt(text: str, max_chars: int = 16000) -> str:
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[중간 생략]...\n\n" + text[-half:]


class PdfTextCache:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._texts: dict[int, str] = {}
        with pdfplumber.open(pdf_path) as pdf:
            self.total_pages = len(pdf.pages)

    def page_text(self, page_no: int) -> str:
        if page_no < 1 or page_no > self.total_pages:
            return ""
        if page_no not in self._texts:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[page_no - 1]
                w, h = page.width, page.height
                mid = w / 2.0
                parts = [clean_text(page.extract_text() or "")]
                # 2단 레이아웃 대응: 좌/우 단을 따로 추출해 함께 보관한다.
                # extract_text가 컬럼을 뒤섞어도, 단별 추출에서는 문단이 이어진다.
                try:
                    left = clean_text(page.crop((0, 0, mid, h)).extract_text() or "")
                    right = clean_text(page.crop((mid, 0, w, h)).extract_text() or "")
                    if left.strip():
                        parts.append("[LEFT]\n" + left)
                    if right.strip():
                        parts.append("[RIGHT]\n" + right)
                except Exception:
                    pass
                # 표도 보조 근거로 추가
                try:
                    for t_idx, table in enumerate(page.extract_tables()):
                        rows = []
                        for row in table:
                            rows.append(
                                " | ".join(clean_text(c or "").replace("\n", " ") for c in row)
                            )
                        rows = [r for r in rows if r.strip(" |")]
                        if rows:
                            parts.append(f"[TABLE {page_no}-{t_idx + 1}]\n" + "\n".join(rows))
                except Exception:
                    pass
                self._texts[page_no] = "\n".join(parts)
        return self._texts[page_no]

    def context_text(self, page_no: int, context_pages: int = 0) -> str:
        start = max(1, page_no - context_pages)
        end = min(self.total_pages, page_no + context_pages)
        blocks = []
        for p in range(start, end + 1):
            blocks.append(f"[PAGE {p}]\n{self.page_text(p)}")
        return "\n\n".join(blocks)

    def search_pages(self, terms: list[str], limit: int = 5) -> list[tuple[int, str]]:
        """모든 terms가 함께 등장하는 페이지를 찾는다."""
        hits: list[tuple[int, str]] = []
        for p in range(1, self.total_pages + 1):
            txt = self.page_text(p)
            if all(term in txt for term in terms):
                hits.append((p, txt))
                if len(hits) >= limit:
                    break
        return hits


def load_riders(json_path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        riders = data
    else:
        riders = data.get("riders", [])
    if not isinstance(riders, list):
        raise ValueError("JSON에 riders 리스트가 없습니다.")

    # pydantic 스키마가 있으면 한 번 검증해서 타입 보정까지 반영한다.
    if ParseResult is not None:
        try:
            result = ParseResult(riders=riders)  # type: ignore
            return [r.model_dump() for r in result.riders]
        except Exception as e:
            print(f"⚠️ rider_schema 검증 실패: {str(e)[:120]} — 원본 dict 기준으로 계속 검수합니다.")
    return riders


def get_source(rider: dict[str, Any]) -> dict[str, Any]:
    src = rider.get("source") or {}
    return src if isinstance(src, dict) else {}


def has_limit_value(rider: dict[str, Any], value: int | str, keyword: str | None = None) -> bool:
    value_s = str(value)
    for lim in rider.get("limits") or []:
        if not isinstance(lim, dict):
            continue
        if str(lim.get("value")) == value_s:
            return True
        note = str(lim.get("note") or "")
        if value_s in note:
            return True
        if keyword and keyword in note:
            return True
    return False


def has_reduction(
    rider: dict[str, Any], days: int | None = None, rate: float | None = None
) -> bool:
    for red in rider.get("reductions") or []:
        if not isinstance(red, dict):
            continue
        ok = True
        if days is not None:
            ok = ok and int(red.get("until_elapsed_days") or -1) == days
        if rate is not None:
            raw_rate = red.get("rate")
            try:
                ok = ok and raw_rate is not None and abs(float(raw_rate) - rate) < 0.001
            except Exception:
                ok = False
        if ok:
            return True
    return False


def local_checks(
    rider: dict[str, Any], pdf: PdfTextCache, context_pages: int = 0
) -> tuple[str, list[Issue], str]:
    issues: list[Issue] = []
    name = str(rider.get("name") or "")
    src = get_source(rider)

    # source.page 확인
    page = src.get("page") or 0
    try:
        page = int(page)
    except Exception:
        page = 0

    if page < 1 or page > pdf.total_pages:
        issues.append(
            Issue(
                "fail",
                "source.page",
                f"source.page={page}가 PDF 범위(1~{pdf.total_pages}) 밖입니다.",
            )
        )
        page_text = ""
    else:
        page_text = pdf.context_text(page, context_pages=context_pages)

    # raw_text 원문 포함 여부
    raw_text = str(src.get("raw_text") or "")
    if not raw_text.strip():
        issues.append(
            Issue(
                "warning",
                "source.raw_text",
                "raw_text가 비어 있습니다. 근거 문장을 원문에서 채워야 합니다.",
                evidence_page=page or None,
            )
        )
    elif page_text:
        nr, npg = norm_text(raw_text), norm_text(page_text)
        if nr in npg:
            pass  # 정상 — 이슈 없음
        elif skeleton(raw_text) and skeleton(raw_text) in skeleton(page_text):
            issues.append(
                Issue(
                    "warning",
                    "source.raw_text",
                    "raw_text의 한글/숫자는 원문과 일치하나 특수문자·로마숫자(Ⅱ 등) 표기가 "
                    "달라 정확 일치하지 않습니다. 가능하면 원문 기호 그대로 맞추세요.",
                    evidence_page=page or None,
                )
            )
        else:
            issues.append(
                Issue(
                    "warning",
                    "source.raw_text",
                    "raw_text를 원문 추출 텍스트에서 찾지 못했습니다. 2단/특수폰트 PDF라 "
                    "추출이 깨졌을 수 있으니, raw_text를 고치기 전에 "
                    "스냅샷·원문과 직접 대조하세요.",
                    evidence_page=page or None,
                )
            )

    # 권장 enum / 스키마 경고
    if Rider is not None:
        try:
            obj = Rider(**rider)  # type: ignore
            for w in obj.warnings():
                issues.append(Issue("warning", "schema", w, evidence_page=page or None))
        except Exception:
            pass
    else:
        trigger_type = str(rider.get("trigger_type") or "")
        unit_type = str(rider.get("unit_type") or "")
        if trigger_type and trigger_type not in TRIGGER_TYPES:
            issues.append(
                Issue("warning", "trigger_type", f"비표준 trigger_type입니다: {trigger_type}")
            )
        if unit_type and unit_type not in UNIT_TYPES:
            issues.append(Issue("warning", "unit_type", f"비표준 unit_type입니다: {unit_type}"))
        for i, lim in enumerate(rider.get("limits") or []):
            if isinstance(lim, dict):
                if lim.get("scope") not in LIMIT_SCOPES:
                    issues.append(
                        Issue(
                            "warning",
                            f"limits[{i}].scope",
                            f"비표준 scope입니다: {lim.get('scope')}",
                        )
                    )
                if lim.get("unit") not in LIMIT_UNITS:
                    issues.append(
                        Issue(
                            "warning", f"limits[{i}].unit", f"비표준 unit입니다: {lim.get('unit')}"
                        )
                    )

    # 휴리스틱 1: 암보장개시일이 있는데 waiting_period_days가 비어 있음
    combined_json_text = " ".join(
        [
            name,
            str(rider.get("trigger_detail") or ""),
            raw_text,
            str(rider.get("unit_basis") or ""),
        ]
    )
    waiting = rider.get("waiting_period_days")
    if "암보장개시일" in combined_json_text and waiting in (None, "", 0):
        hits = pdf.search_pages(["암보장개시일", "90일"], limit=3)
        suggested = 90 if hits else "암보장개시일 정의 확인 필요"
        ev_page = hits[0][0] if hits else (page or None)
        issues.append(
            Issue(
                "warning",
                "waiting_period_days",
                "지급사유에 '암보장개시일'이 있는데 waiting_period_days가 비어 있습니다. "
                "암보장개시일 정의를 확인하세요.",
                suggested_value=suggested,
                evidence_page=ev_page,
            )
        )

    # 휴리스틱 2: 2년/50% 감액 조건 누락 의심
    local_text = page_text + "\n" + combined_json_text
    if ("2년" in local_text or "730" in local_text) and (
        "50%" in local_text or "50％" in local_text or "50퍼센트" in local_text
    ):
        if not has_reduction(rider, days=730, rate=0.5):
            issues.append(
                Issue(
                    "warning",
                    "reductions",
                    "원문/근거에 2년 미만 50% 감액 조건이 보이지만 "
                    "reductions에 730일/0.5가 없습니다.",
                    suggested_value={"until_elapsed_days": 730, "rate": 0.5},
                    evidence_page=page or None,
                )
            )

    # 휴리스틱 3: 최초 1회 한도 누락 의심
    if "최초 1회" in local_text and not has_limit_value(rider, 1, keyword="최초"):
        issues.append(
            Issue(
                "warning",
                "limits",
                "원문/근거에 '최초 1회'가 보이지만 limits에 최초 1회 한도가 명확히 없습니다.",
                suggested_value={"scope": "lifetime", "unit": "count", "value": 1},
                evidence_page=page or None,
            )
        )

    # 휴리스틱 4: 입원 180일 한도 누락 의심
    if "입원" in local_text and "180일" in local_text and not has_limit_value(rider, 180):
        issues.append(
            Issue(
                "warning",
                "limits",
                "입원 관련 원문에 180일 한도가 보이지만 limits에 180일 한도가 없습니다.",
                suggested_value={"unit": "days", "value": 180},
                evidence_page=page or None,
            )
        )

    # 휴리스틱 5: 4일째부터 지급인데 deduct_days 누락 의심
    if ("4일째부터" in local_text or "4일 이상" in local_text) and int(
        rider.get("deduct_days") or 0
    ) == 0:
        issues.append(
            Issue(
                "warning",
                "deduct_days",
                "원문에 4일째부터/4일 이상 조건이 보이지만 deduct_days가 0입니다. "
                "4일째부터 지급이면 deduct_days=3인지 확인하세요.",
                suggested_value=3,
                evidence_page=page or None,
            )
        )

    status = (
        "fail" if any(i.severity == "fail" for i in issues) else ("warning" if issues else "pass")
    )
    return status, issues, page_text


VERIFY_SYSTEM_PROMPT = """너는 보험 약관 JSON 검수자다.
아래에는 PDF에서 추출한 약관 원문 텍스트와, 그 원문에서 추출된 rider JSON 1개가 있다.
JSON의 각 필드가 원문에 근거하는지 검수하라.

검수 기준:
1. 원문에 없는 금액/기간/한도/지급조건을 JSON이 만들어냈으면 fail.
2. 면책기간, 감액기간, 지급한도, 지급 시작일, 제외사항이 원문에 있는데 JSON에 빠졌으면 warning.
3. raw_text가 원문과 문장/기호/띄어쓰기/줄바꿈이 달라 그대로 인용하기 어렵다면 warning.
4. trigger_type이 지급사유와 명백히 다르면 fail.
5. 판단이 애매하면 fail이 아니라 warning으로 표시하라.
6. verified=true 여부는 판단하지 말라. 사람 검수 전에는 verified=false가 정상이다.

반드시 아래 JSON 형식만 출력하라. 설명문, 마크다운, 코드펜스는 쓰지 마라.
{
  "status": "pass" | "warning" | "fail",
  "issues": [
    {
      "severity": "warning" | "fail",
      "field": "필드명",
      "message": "문제 설명",
      "suggested_value": "수정 제안 또는 null",
      "evidence_quote": "근거가 되는 짧은 원문 또는 null"
    }
  ]
}
"""


def parse_json_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM 응답에서 JSON 객체를 찾지 못했습니다.")
    return json.loads(cleaned[start : end + 1])


def call_llm_verify(rider: dict[str, Any], page_text: str, model: str) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic()
    user_prompt = (
        "[약관 원문 텍스트]\n"
        + compact_for_prompt(page_text, max_chars=18000)
        + "\n\n[검수 대상 rider JSON]\n"
        + json.dumps(rider, ensure_ascii=False, indent=2)
    )
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0,
        system=VERIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    # content는 블록 유니온(text/thinking/tool_use…) → text 블록만 좁혀서 .text 접근
    block = msg.content[0]
    if block.type != "text":
        raise RuntimeError(f"예상치 못한 응답 블록 타입: {block.type}")
    return parse_json_from_text(block.text)


def merge_llm_issues(
    local_issues: list[Issue], llm_result: dict[str, Any] | None
) -> tuple[str, list[dict[str, Any]]]:
    issues = [i.to_dict() for i in local_issues]
    if llm_result:
        for item in llm_result.get("issues") or []:
            if not isinstance(item, dict):
                continue
            issues.append(
                {
                    "severity": item.get("severity")
                    or ("fail" if llm_result.get("status") == "fail" else "warning"),
                    "field": item.get("field") or "llm",
                    "message": item.get("message") or "LLM 검수 이슈",
                    "suggested_value": item.get("suggested_value"),
                    "evidence_quote": item.get("evidence_quote"),
                    "source": "llm",
                }
            )
    status = (
        "fail"
        if any(i.get("severity") == "fail" for i in issues)
        else ("warning" if issues else "pass")
    )
    return status, issues


def write_markdown(report: dict[str, Any], md_path: Path) -> None:
    lines = []
    s = report["summary"]
    lines.append("# 약관 JSON 자동 검수 리포트\n")
    lines.append(f"- PDF: `{report['pdf']}`")
    lines.append(f"- JSON: `{report['json']}`")
    lines.append(f"- 총 보장: {s['total']}")
    lines.append(f"- PASS: {s['pass']} / WARNING: {s['warning']} / FAIL: {s['fail']}")
    lines.append(f"- LLM 호출: {s['llm_called']}\n")
    for item in report["results"]:
        if item["status"] == "pass":
            continue
        lines.append(
            f"## {item['status'].upper()} — {item['rider_name']} (p.{item.get('source_page')})"
        )
        for issue in item.get("issues") or []:
            msg = issue.get("message", "")
            field = issue.get("field", "")
            sev = issue.get("severity", "warning")
            sug = issue.get("suggested_value")
            lines.append(f"- `{sev}` `{field}`: {msg}")
            if sug not in (None, ""):
                lines.append(f"  - suggested_value: `{json.dumps(sug, ensure_ascii=False)}`")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="약관 파싱 JSON 자동 검수 보조 도구")
    ap.add_argument("pdf", help="원본 약관 PDF")
    ap.add_argument("json", help="parse_policy.py / parse_rider.py 출력 JSON")
    ap.add_argument("--out", default=None, help="검수 리포트 JSON 저장 경로")
    ap.add_argument("--md-out", default=None, help="검수 리포트 Markdown 저장 경로")
    ap.add_argument(
        "--context-pages",
        type=int,
        default=0,
        help="source.page 앞뒤 몇 페이지까지 원문 비교에 넣을지",
    )
    ap.add_argument("--limit", type=int, default=0, help="앞에서 N개 보장만 검수 테스트")
    ap.add_argument("--llm", action="store_true", help="Anthropic API로 AI 검수 추가 수행")
    ap.add_argument(
        "--llm-scope",
        choices=["warnings", "all"],
        default="warnings",
        help="AI 검수 대상: warnings=로컬 경고/실패만, all=전체",
    )
    ap.add_argument(
        "--model",
        default="claude-haiku-4-5",
        help="AI 검수 모델. 실패 시 claude-sonnet-4-6 등으로 변경",
    )
    ap.add_argument("--sleep", type=float, default=0.5, help="LLM 호출 사이 대기초")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    json_path = Path(args.json)
    if not pdf_path.exists():
        sys.exit(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    if not json_path.exists():
        sys.exit(f"JSON 파일을 찾을 수 없습니다: {json_path}")

    riders = load_riders(str(json_path))
    if args.limit:
        riders = riders[: args.limit]

    pdf = PdfTextCache(str(pdf_path))
    results = []
    llm_called = 0

    print(f"[1/2] 로컬 검수 시작 — 보장 {len(riders)}개, PDF {pdf.total_pages}페이지")
    for idx, rider in enumerate(riders, 1):
        name = str(rider.get("name") or f"rider-{idx}")
        src = get_source(rider)
        page = src.get("page") or 0
        try:
            page = int(page)
        except Exception:
            page = 0

        local_status, local_issues, page_text = local_checks(
            rider, pdf, context_pages=args.context_pages
        )
        llm_result = None

        should_llm = False
        if args.llm:
            should_llm = args.llm_scope == "all" or local_status in {"warning", "fail"}

        if should_llm:
            print(f"[2/2] AI 검수 {idx}/{len(riders)} — {name} ...", flush=True)
            try:
                # source.page가 잘못되면 빈 텍스트 대신 앞뒤 없이 가능한 페이지 범위만 사용
                if not page_text and 1 <= page <= pdf.total_pages:
                    page_text = pdf.context_text(page, context_pages=args.context_pages)
                llm_result = call_llm_verify(rider, page_text, args.model)
                llm_called += 1
            except Exception as e:
                local_issues.append(Issue("warning", "llm", f"AI 검수 호출 실패: {str(e)[:180]}"))
            time.sleep(args.sleep)

        final_status, final_issues = merge_llm_issues(local_issues, llm_result)
        results.append(
            {
                "rider_name": name,
                "source_page": page,
                "status": final_status,
                "issues": final_issues,
                "local_status": local_status,
                "llm_status": llm_result.get("status") if isinstance(llm_result, dict) else None,
            }
        )

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warning": sum(1 for r in results if r["status"] == "warning"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "llm_called": llm_called,
    }
    report = {
        "pdf": str(pdf_path),
        "json": str(json_path),
        "verified_policy": (
            "AI/로컬 검수 pass는 verified=true가 아닙니다. "
            "사람 검수 완료 후에만 verified=true로 변경하세요."
        ),
        "summary": summary,
        "results": results,
    }

    out_path = Path(args.out or json_path.with_name(json_path.stem + "_verify_report.json"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = Path(args.md_out) if args.md_out else out_path.with_suffix(".md")
    write_markdown(report, md_path)

    print("\n[완료]")
    print(
        f"  total={summary['total']} pass={summary['pass']} "
        f"warning={summary['warning']} fail={summary['fail']} "
        f"llm_called={summary['llm_called']}"
    )
    print(f"  JSON 리포트: {out_path}")
    print(f"  MD 리포트:   {md_path}")
    if summary["warning"] or summary["fail"]:
        print("\n  우선 확인할 항목:")
        shown = 0
        for r in results:
            if r["status"] == "pass":
                continue
            first = (r.get("issues") or [{}])[0]
            print(
                f"   · {r['status'].upper()} {r['rider_name']} "
                f"(p.{r.get('source_page')}): {first.get('field')} — {first.get('message')}"
            )
            shown += 1
            if shown >= 10:
                rest = summary["warning"] + summary["fail"] - shown
                if rest > 0:
                    print(f"   · ... 외 {rest}건")
                break


if __name__ == "__main__":
    main()
