"""사용자 업로드 약관 PDF 처리 서비스 (온디맨드 파싱 방식).

업로드 시: pdfplumber 텍스트 추출 → policy_pages 저장 → 완료 (~5원, LLM 없음)
쿼리 시:   키워드로 관련 페이지 필터 → GPT-4.1-mini 구조화 파싱 → riders/rider_chunks 생성 → 캐시
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
from pathlib import Path

import pdfplumber
from openai import OpenAI

from app.config import settings
from app.core.errors import NotFoundError
from app.db import get_client
from app.rag.chunker import chunk_rider
from app.rag.embedder import embed

# 저장소 루트 기준 프롬프트 경로
# backend/app/services/user_policy_service.py → parents[3] = bojang 루트
_ROOT = Path(__file__).resolve().parents[3]
_PROMPT_PATH = _ROOT / "prompts" / "parsing" / "rider_extraction_prompt.txt"

# 온디맨드 파싱 모델
_PARSE_MODEL = "gpt-4.1-mini"

# PDF 업로드 제한
_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB

# treatment_types.code → 약관 키워드 매핑 (005_treatment_tables.sql aliases 기준)
TREATMENT_KEYWORDS: dict[str, list[str]] = {
    "MRI_MRA": ["MRI", "MRA", "자기공명영상", "MRI촬영", "자기공명영상진단"],
    "CT": ["CT", "CT촬영", "전산화단층촬영"],
    "XRAY": ["X-ray", "엑스레이", "방사선촬영", "단순방사선"],
    "MANUAL_THERAPY": ["도수치료", "도수", "수기치료"],
    "PHYSICAL_THERAPY": ["물리치료", "물리요법"],
    "ECSWT": ["체외충격파", "ECSWT", "충격파치료"],
    "INJECTION": ["주사", "주사치료", "주사료", "비급여주사"],
    "MEDICATION": ["약 처방", "투약", "약제비", "처방약"],
    "CAST": ["깁스", "석고붕대", "통깁스"],
    "BRACE_SPLINT": ["보조기", "부목", "스플린트"],
    "EMERGENCY": ["응급실", "응급", "응급진료", "응급내원"],
    # visit_type 정규화용 (아래 _normalize_items 참고)
    "INPATIENT": ["입원", "입원일당", "입원비"],
    "OUTPATIENT": ["외래", "통원", "통원치료"],
    "SURGERY": ["수술", "수술비", "수술급여금"],
}


def _get_openai() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def _make_query_hash(
    policy_id: str,
    disease_kcd: str,
    disease_name: str,
    normalized_items: list[str],
) -> str:
    """정규화된 입력값 기반 결정론적 MD5 해시 생성 (캐시 키).

    visit_type/surgery 는 _normalize_items() 에서 이미 normalized_items 에 통합됐으므로
    별도 필드 없이 items 만 해시에 포함한다.
    이렇게 해야 아래 두 요청이 동일 캐시 키를 공유한다:
      {"treatment_items": ["EMERGENCY"], "visit_type": null}
      {"treatment_items": [],            "visit_type": "EMERGENCY"}
    """
    payload = {
        "policy_id": policy_id,
        "kcd": disease_kcd.upper(),
        "name": disease_name.strip(),
        "items": sorted(normalized_items),
    }
    return hashlib.md5(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _normalize_items(
    treatment_items: list[str],
    visit_type: str | None,
    surgery: bool | None,
) -> list[str]:
    """visit_type, surgery를 treatment_items 코드셋으로 정규화.

    TREATMENT_KEYWORDS 키워드 검색에 모든 조건이 반영되도록
    visit_type과 surgery를 treatment_items 리스트에 포함시킨다.
    """
    items: set[str] = {t.upper() for t in (treatment_items or [])}

    if visit_type:
        items.add(visit_type.upper())  # INPATIENT / OUTPATIENT / EMERGENCY 등

    if surgery is True:
        items.add("SURGERY")

    return list(items)


# ──────────────────────────────────────────────
# 1. 업로드 단계
# ──────────────────────────────────────────────


def _clean(text: str) -> str:
    """pdfplumber 추출 텍스트 정리 (NUL·NBSP 제거)."""
    return text.replace("\x00", " ").replace("\xa0", " ")


def extract_pages(pdf_bytes: bytes) -> list[dict]:
    """PDF 바이트에서 페이지별 텍스트 + 표를 추출한다.

    반환: [{"page_num": 1, "text": "..."}, ...]
    """
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            blocks = [f"[PAGE {i}]"]
            raw = page.extract_text() or ""
            blocks.append(_clean(raw))
            for t_idx, table in enumerate(page.extract_tables()):
                rows = [" | ".join(_clean(c or "").replace("\n", " ") for c in row) for row in table]
                rows = [r for r in rows if r.strip(" |")]
                if rows:
                    blocks.append(f"[TABLE {i}-{t_idx + 1}] (보조)\n" + "\n".join(rows))
            pages.append({"page_num": i, "text": "\n\n".join(blocks)})
    return pages


def upload_pdf(user_id: str, file_name: str, pdf_bytes: bytes) -> dict:
    """PDF 업로드 처리.

    1. PDF 기본 검증 (크기, 매직바이트, 페이지 수, 빈 텍스트)
    2. policies 행 생성 (is_preset=False)
    3. policy_pages 에 페이지별 텍스트 저장
    실패 시 생성된 policies 행을 롤백(삭제)한다.

    반환: {"policy_id": str, "page_count": int}
    """
    # ── PDF 기본 검증 ──
    if len(pdf_bytes) > _MAX_PDF_BYTES:
        raise ValueError(f"PDF 크기 제한 초과 (최대 {_MAX_PDF_BYTES // (1024 * 1024)}MB)")
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("유효한 PDF 파일이 아닙니다.")

    db = get_client()
    policy_id = str(uuid.uuid4())

    # ── 1. policies 행 생성 ──
    # pdf_path: Supabase Storage 업로드 미구현 상태. 향후 원본 저장 시 채워질 경로.
    db.table("policies").insert(
        {
            "id": policy_id,
            "name": file_name.replace(".pdf", "").replace("_", " "),
            "insurer": "직접업로드",
            "type": "질병",  # TODO: PDF 첫 페이지 분석 후 type 자동 감지
            "is_preset": False,
            "user_id": user_id,
            "pdf_path": None,  # 원본 PDF Storage 업로드 미구현 — null 유지
        }
    ).execute()

    try:
        # ── 2. 텍스트 추출 ──
        pages = extract_pages(pdf_bytes)

        # 스캔 PDF 감지: 텍스트 50자 미만 페이지가 절반 이상이면 거부
        empty_count = sum(1 for p in pages if len(p["text"].strip()) < 50)
        if empty_count > len(pages) * 0.5:
            raise ValueError(
                "텍스트 추출 실패 — 스캔 이미지 PDF는 지원되지 않습니다. 텍스트 레이어가 포함된 PDF를 업로드해주세요."
            )

        # ── 3. policy_pages 저장 (100행씩 배치) ──
        page_rows = [{"policy_id": policy_id, "page_num": p["page_num"], "text": p["text"]} for p in pages]
        for i in range(0, len(page_rows), 100):
            db.table("policy_pages").insert(page_rows[i : i + 100]).execute()

    except Exception:
        # 롤백: orphan policies 행 제거
        db.table("policies").delete().eq("id", policy_id).execute()
        raise

    return {"policy_id": policy_id, "page_count": len(pages)}


# ──────────────────────────────────────────────
# 2. 쿼리 단계: 키워드 필터 → LLM 파싱 → 캐시
# ──────────────────────────────────────────────


def _build_keywords(
    disease_kcd: str,
    disease_name: str,
    treatment_items: list[str] | None = None,
) -> list[str]:
    """KCD 코드·질병명·처치 항목에서 약관 검색 키워드를 생성한다.

    treatment_items 는 _normalize_items() 를 거쳐 visit_type/surgery 포함 정규화된 값이어야 한다.
    """
    keywords: list[str] = []

    # KCD 코드 자체 + 앞 2자 범주
    if disease_kcd:
        keywords.append(disease_kcd.upper())
        keywords.append(disease_kcd[:2].upper())

    # 질병명 토크나이징
    if disease_name:
        keywords.append(disease_name)
        for word in re.split(r"[\s,\(\)·]", disease_name):
            if len(word) >= 2:
                keywords.append(word)

    # KCD 대분류별 약관 키워드
    kcd_upper = disease_kcd.upper() if disease_kcd else ""
    if kcd_upper.startswith("I6"):
        keywords += ["뇌혈관", "뇌졸중", "뇌경색", "뇌출혈"]
    elif kcd_upper.startswith("I2"):
        keywords += ["심근경색", "급성심근경색", "심장", "허혈성심장질환", "허혈성"]
    elif kcd_upper.startswith(("C", "D0", "D1", "D2", "D3", "D4")):
        keywords += ["암", "악성신생물", "암진단"]
    elif kcd_upper.startswith("M5"):
        keywords += ["디스크", "추간판", "척추"]

    # 처치 항목 키워드 (DB treatment_types.code 기준)
    for item in treatment_items or []:
        keywords += TREATMENT_KEYWORDS.get(item.upper(), [])

    return list(dict.fromkeys(keywords))  # 중복 제거, 순서 유지


def find_relevant_pages(
    policy_id: str,
    keywords: list[str],
    max_pages: int = 15,
) -> list[dict]:
    """policy_pages 에서 키워드가 포함된 페이지(±1 컨텍스트 포함)를 반환한다.

    반환: [{"page_num": int, "text": str}, ...]  최대 max_pages 개
    """
    db = get_client()
    res = db.table("policy_pages").select("page_num, text").eq("policy_id", policy_id).order("page_num").execute()
    all_pages = res.data or []
    page_map: dict[int, dict] = {row["page_num"]: row for row in all_pages}

    # 키워드 히트 페이지 + ±1 컨텍스트 수집
    hit_page_nums: set[int] = set()
    for row in all_pages:
        if any(kw in row["text"] for kw in keywords):
            n = row["page_num"]
            hit_page_nums.update([n - 1, n, n + 1])

    # 유효 페이지만 필터
    valid = [n for n in hit_page_nums if n in page_map]

    # 점수(히트 키워드 수) 내림차순으로 max_pages 선택 후 page_num 순 정렬
    scored = sorted(
        ((sum(1 for kw in keywords if kw in page_map[n]["text"]), n) for n in valid),
        reverse=True,
    )
    selected = sorted(n for _, n in scored[:max_pages])

    return [page_map[n] for n in selected]


def _parse_pages_with_llm(pages: list[dict]) -> list[dict]:
    """선별된 페이지를 LLM(GPT-4.1-mini)으로 구조화 파싱한다.

    파싱 실패 시 ValueError 발생 (빈 리스트 묵인 없음).
    반환: riders 리스트 (Rider 스키마 구조)
    """
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"프롬프트 파일 없음: {_PROMPT_PATH}")

    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    document = "\n\n".join(p["text"] for p in pages)

    client = _get_openai()
    msg = client.chat.completions.create(
        model=_PARSE_MODEL,
        max_tokens=8000,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "다음 약관 추출 텍스트에서 보장(rider)을 구조화하세요. JSON 객체만 출력하세요.\n\n" + document
                ),
            },
        ],
    )
    raw = msg.choices[0].message.content or ""

    # JSON 파싱 (백틱 펜스 방어)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1].removeprefix("json").strip()
    brace = cleaned.find("{")
    if brace == -1:
        raise ValueError(f"LLM 파싱 실패 — JSON 없음. 응답: {raw[:300]!r}")
    cleaned = cleaned[brace : cleaned.rfind("}") + 1]

    try:
        data = json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM 파싱 실패 — JSON 파싱 에러: {e}. 응답: {cleaned[:300]!r}") from e

    riders = data.get("riders", [])
    if not isinstance(riders, list):
        raise ValueError(f"LLM 파싱 실패 — riders 필드가 리스트가 아님: {type(riders)}")

    return riders


def _save_riders(policy_id: str, query_hash: str, riders_raw: list[dict]) -> list[str]:
    """파싱된 riders를 DB에 저장하고 rider_chunks + 임베딩도 생성한다.

    query_hash를 parse_query_hash 컬럼에 저장해 시나리오별 riders를 구분한다.
    반환: 생성된 rider_id 목록
    """
    db = get_client()
    rider_ids = []

    for r in riders_raw:
        rider_id = str(uuid.uuid4())
        rider_row = {
            "id": rider_id,
            "policy_id": policy_id,
            "parse_query_hash": query_hash,
            "name": r.get("name", ""),
            "is_main": r.get("is_main", False),
            "trigger_type": r.get("trigger_type", "기타"),
            "trigger_detail": r.get("trigger_detail", ""),
            "unit_amount": r.get("unit_amount"),
            "unit_type": r.get("unit_type", "기타"),
            "unit_basis": r.get("unit_basis"),
            "boundaries": r.get("boundaries", []),
            "exclusions": r.get("exclusions", []),
            "limits": r.get("limits", []),
            "waiting_period_days": r.get("waiting_period_days"),
            "reductions": r.get("reductions", []),
            "deduct_days": r.get("deduct_days", 0) or 0,
            "claim_rule": r.get("claim_rule"),
            "source_pages": r.get("source_pages", []),
            "article_no": (r.get("source") or {}).get("article", ""),
            "page": (r.get("source") or {}).get("page"),
            "raw_text": (r.get("source") or {}).get("raw_text", ""),
            "verified": False,
            "coverage_kind": "실손" if r.get("claim_rule") else "정액",
        }
        db.table("riders").insert(rider_row).execute()

        # rider_chunks 생성 + 임베딩
        chunks = chunk_rider({**rider_row, "id": rider_id})
        if chunks:
            texts = [c["content"] for c in chunks]
            embeddings = embed(texts)
            for c, emb in zip(chunks, embeddings, strict=True):
                c["rider_id"] = rider_id
                c["embedding"] = emb
                db.table("rider_chunks").insert(c).execute()

        rider_ids.append(rider_id)

    return rider_ids


def get_or_parse_riders(
    user_id: str,
    policy_id: str,
    disease_kcd: str,
    disease_name: str,
    treatment_items: list[str] | None = None,
    visit_type: str | None = None,
    surgery: bool | None = None,
) -> list[dict]:
    """캐시 우선: (policy_id, query_hash) 캐시 히트 시 해당 hash의 riders만 반환.
    캐시 미스 시 온디맨드 파싱 후 저장.

    Raises:
        NotFoundError: policy_id 없음 또는 페이지 데이터 없음
        PermissionError: 다른 사용자의 약관에 접근 시도
        ValueError: LLM 파싱 실패
    """
    db = get_client()

    # ── 소유자 검증 ──
    policy_res = db.table("policies").select("id, user_id, is_preset").eq("id", policy_id).single().execute()
    if not policy_res.data:
        raise NotFoundError(f"policy_id={policy_id} 를 찾을 수 없습니다.")
    if not policy_res.data.get("is_preset") and policy_res.data.get("user_id") != user_id:
        raise PermissionError("해당 약관에 대한 접근 권한이 없습니다.")

    # ── visit_type, surgery → treatment_items 정규화 ──
    normalized_items = _normalize_items(treatment_items, visit_type, surgery)

    # ── query_hash 생성 (정규화된 items만 사용 — visit_type/surgery 중복 방지) ──
    q_hash = _make_query_hash(policy_id, disease_kcd, disease_name, normalized_items)

    # ── 캐시 확인 (query_hash 기반) ──
    cache_res = (
        db.table("policy_parse_cache").select("id").eq("policy_id", policy_id).eq("query_hash", q_hash).execute()
    )
    if cache_res.data:
        # 캐시 hit: 이 query_hash로 저장된 riders만 반환 (다른 시나리오 riders 제외)
        existing = db.table("riders").select("*").eq("policy_id", policy_id).eq("parse_query_hash", q_hash).execute()
        return existing.data or []

    # ── 관련 페이지 키워드 필터 ──
    keywords = _build_keywords(disease_kcd, disease_name, normalized_items)
    relevant_pages = find_relevant_pages(policy_id, keywords)

    if not relevant_pages:
        # 키워드 미매칭 시 앞 20페이지 폴백
        res = (
            db.table("policy_pages")
            .select("page_num, text")
            .eq("policy_id", policy_id)
            .order("page_num")
            .limit(20)
            .execute()
        )
        relevant_pages = res.data or []

    if not relevant_pages:
        raise NotFoundError(f"policy_id={policy_id} 에 저장된 페이지 데이터가 없습니다. 먼저 PDF를 업로드해주세요.")

    # ── LLM 파싱 (실패 시 예외 전파) ──
    riders_raw = _parse_pages_with_llm(relevant_pages)

    # ── DB 저장 (rider + rider_chunks + embedding) ──
    if riders_raw:
        _save_riders(policy_id, q_hash, riders_raw)

    # ── 캐시 등록 (동시 요청 충돌 방어) ──
    # 거의 동시에 두 요청이 cache miss → 두 번 파싱 → unique 충돌이 발생할 수 있다.
    # 충돌 시 두 번째 요청은 이미 저장된 riders를 재조회해서 반환한다.
    try:
        db.table("policy_parse_cache").insert(
            {
                "policy_id": policy_id,
                "query_hash": q_hash,
            }
        ).execute()
    except Exception:
        # 다른 요청이 먼저 캐시를 만든 경우 — 그 riders 재조회 후 반환
        existing = db.table("riders").select("*").eq("policy_id", policy_id).eq("parse_query_hash", q_hash).execute()
        return existing.data or []

    # ── 저장 후 재조회 (이 hash의 riders만) ──
    saved = db.table("riders").select("*").eq("policy_id", policy_id).eq("parse_query_hash", q_hash).execute()
    return saved.data or []
