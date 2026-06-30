"""보장 서비스 MCP 서버.

마켓플레이스에 공급자 서버로 등록할 때 실행하는 독립 프로세스다.
Supabase의 공개/공시실 기반 프리셋 보험 데이터로 조회와 간단 분석 도구를 제공한다.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from supabase import Client, create_client

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")
if os.getenv("DEBUG", "").lower() not in ["", "0", "1", "true", "false", "yes", "no", "on", "off"]:
    os.environ["DEBUG"] = "true"

HOST = os.getenv("BOJANG_MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("BOJANG_MCP_PORT", "8101"))
MCP_DEMO_USER_ID = os.getenv("BOJANG_MCP_DEMO_USER_ID", "00000000-0000-0000-0000-000000000000")
INJURY_PART_PATTERN = r"(손가락|발가락|손목|발목|무릎|어깨|허리|팔꿈치|팔|다리|손|발)"
INJURY_KEYWORDS = [
    "다쳤",
    "다쳐",
    "다친",
    "다침",
    "상해",
    "골절",
    "삐었",
    "부러졌",
    "찢어",
    "찢어져",
    "찢어짐",
    "베였",
    "베임",
    "꼬맸",
    "꿰맸",
    "봉합",
    "깁스",
    "기브스",
    "부목",
]

mcp = FastMCP("Bojang MCP", host=HOST, port=PORT)


@mcp.tool()
def service_overview() -> dict[str, object]:
    """보험금 청구 가능 보장 탐색 서비스의 핵심 기능을 요약한다."""
    return {
        "service": "Bojang",
        "summary": "보험 가입 정보와 질병·입원 정보를 바탕으로 청구 가능한 보장을 찾고 약관 근거를 함께 제시합니다.",
        "main_features": [
            "보험 약관 PDF 업로드 및 페이지 텍스트 추출",
            "질병·입원·수술 조건 기반 보장 후보 검색",
            "약관 원문 근거와 함께 예상 보험금 판정",
            "여러 시나리오의 보장 금액 비교",
        ],
    }


@mcp.tool()
def list_public_policies(
    query: Annotated[
        str | None,
        Field(
            description="보험명, 보험사, 보험 유형 검색어입니다. 예: 암, 실손, 현대해상. 비워두면 전체 일부를 보여줍니다."
        ),
    ] = None,
    limit: Annotated[int, Field(ge=1, le=20, description="가져올 최대 보험 개수입니다. 기본값은 10개입니다.")] = 10,
) -> dict[str, object]:
    """Supabase의 공시실/프리셋 보험 목록을 조회한다."""
    try:
        policies = _fetch_public_policies(query=query, limit=limit)
    except Exception as exc:
        return _supabase_error("PUBLIC_POLICIES_UNAVAILABLE", exc)

    return {
        "policies": policies,
        "note": "Supabase policies 테이블의 is_preset=true 공개/공시실 기반 보험만 조회했습니다.",
    }


@mcp.tool()
def public_claim_flow(
    situation: Annotated[
        str,
        Field(description="사용자가 말한 청구 상황입니다. 예: 갑상선암 진단받았어요, 손목을 다쳐 통원 치료받았어요."),
    ],
    policy_id: Annotated[
        str | None,
        Field(description="분석할 공시실/프리셋 보험 ID입니다. 모르면 상황에 맞는 후보 보험을 자동 분석합니다."),
    ] = None,
) -> dict[str, object]:
    """자연어 상황을 웹사이트의 케이스·대시보드·판정 파이프라인으로 분석한다."""
    understood = _understand_situation(situation)
    selected_policy_ids = [policy_id] if policy_id else _select_mcp_policy_ids(situation, understood)

    if not selected_policy_ids:
        return {
            "error": "NO_PUBLIC_POLICY",
            "message": "분석할 공개/프리셋 보험을 찾지 못했습니다.",
            "understood": understood,
        }

    try:
        from app.services import analysis_service, case_service

        case_result = case_service.create_case(
            MCP_DEMO_USER_ID,
            "CASE1",
            selected_policy_ids,
            situation,
        )
        case_id = case_result.get("case_id")
        if not case_id:
            return {
                "step": "unsupported",
                "understood": understood,
                "message": case_result.get("message") or "지원 범위 밖 상황입니다.",
            }

        dashboard_patch = _build_mcp_dashboard_patch(situation, understood, case_result)
        if dashboard_patch:
            case_service.patch_dashboard(MCP_DEMO_USER_ID, str(case_id), dashboard_patch)

        dashboard = case_service.get_dashboard(MCP_DEMO_USER_ID, str(case_id))
        analysis = analysis_service.search_analysis(MCP_DEMO_USER_ID, str(case_id))
    except Exception as exc:
        return _supabase_error("WEBSITE_PIPELINE_FAILED", exc)

    return {
        "step": "website_pipeline_analysis",
        "case_id": case_id,
        "understood": understood,
        "selected_policy_ids": selected_policy_ids,
        "dashboard": dashboard.get("dashboard"),
        "analysis_summary": analysis.get("summary"),
        "possible_coverages": _summarize_search_results(analysis.get("results") or []),
        "case2_summary": analysis.get("case2_summary"),
        "notice": analysis.get("notice"),
        "message": "MCP 전용 데모 사용자로 웹사이트의 case_service → analysis_service 파이프라인을 실행했습니다.",
    }


@mcp.tool()
def claim_documents(
    claim_type: Annotated[
        Literal["입원", "수술", "통원", "진단"],
        Field(description="준비 서류를 확인할 보험금 청구 유형입니다."),
    ] = "입원",
) -> dict[str, object]:
    """청구 유형별로 일반적으로 필요한 서류를 안내한다."""
    common = ["보험금 청구서", "신분증 사본", "진료비 영수증", "진료비 세부산정내역서"]
    by_type = {
        "입원": ["입퇴원확인서", "진단서 또는 진료확인서"],
        "수술": ["수술확인서", "진단서"],
        "통원": ["통원확인서 또는 진료확인서", "처방전"],
        "진단": ["진단서", "검사결과지"],
    }
    return {
        "claim_type": claim_type,
        "documents": common + by_type[claim_type],
        "note": "보험사와 담보별로 추가 서류가 다를 수 있어 실제 약관·청구 안내를 확인해야 합니다.",
    }


def _extract_admitted_days(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:일|일간|박)\s*입원", text)
    if match:
        return int(match.group(1))

    match = re.search(r"입원\s*(\d+)\s*(?:일|일간|박)", text)
    if match:
        return int(match.group(1))

    return None


def _extract_disease_name(text: str) -> str | None:
    match = re.search(r"(.+?)(?:으로|로)\s*\d+\s*(?:일|일간|박)\s*입원", text)
    if match:
        return match.group(1).strip()

    match = re.search(r"([가-힣A-Za-z0-9\s]+암)(?:으로|로|을|를|이|가|\s|$)", text)
    if match:
        return match.group(1).strip()

    match = re.search(r"([가-힣A-Za-z0-9\s]+(?:골절|염좌|화상|파열|타박상))(?:으로|로|을|를|이|가|\s|$)", text)
    if match:
        return match.group(1).strip()

    injury_match = re.search(
        rf"{INJURY_PART_PATTERN}.*({'|'.join(INJURY_KEYWORDS)})",
        text,
    )
    if injury_match:
        return f"{injury_match.group(1)} 상해"

    for keyword in ["허리디스크", "갑상선암", "폐렴", "골절", "암", "백내장", "독감"]:
        if keyword in text:
            return keyword

    return None


@lru_cache(maxsize=1)
def _get_public_db() -> Client:
    load_dotenv(BACKEND_ROOT / ".env")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 없습니다.")
    return create_client(supabase_url, supabase_key)


def _fetch_public_policies(query: str | None = None, limit: int = 10) -> list[dict[str, object]]:
    db = _get_public_db()
    res = (
        db.table("policies")
        .select("id,name,insurer,type,is_preset")
        .eq("is_preset", True)
        .limit(max(limit * 3, limit))
        .execute()
    )
    rows = res.data or []

    if query:
        normalized = query.replace("보험", "").strip().lower()
        rows = [
            row
            for row in rows
            if normalized in " ".join(str(row.get(key) or "") for key in ["name", "insurer", "type"]).lower()
        ]

    return [
        {
            "policy_id": row.get("id"),
            "name": row.get("name"),
            "insurer": row.get("insurer"),
            "type": row.get("type"),
        }
        for row in rows[:limit]
    ]


def _analyze_public_policy_claim(
    policy_id: str,
    situation: str,
    understood: dict[str, object],
) -> dict[str, object]:
    db = _get_public_db()
    policy_res = (
        db.table("policies")
        .select("id,name,insurer,type,is_preset")
        .eq("id", policy_id)
        .eq("is_preset", True)
        .maybe_single()
        .execute()
    )
    if not policy_res.data:
        return {
            "error": "UNKNOWN_PUBLIC_POLICY",
            "message": "해당 policy_id의 공개/프리셋 보험을 찾지 못했습니다.",
        }

    riders_res = (
        db.table("riders")
        .select(
            "id,policy_id,name,trigger_type,trigger_detail,unit_amount,unit_type,unit_basis,page,article_no,raw_text,coverage_kind"
        )
        .eq("policy_id", policy_id)
        .limit(240)
        .execute()
    )
    riders = riders_res.data or []

    scored = sorted(
        (_score_rider(row, situation, understood) for row in riders),
        key=lambda item: item["score"],
        reverse=True,
    )
    candidates = [item for item in scored if item["score"] > 0][:5] or scored[:5]

    enriched = []
    for item in candidates:
        rider = item["rider"]
        source = _fetch_rider_source(db, str(rider.get("id")))
        enriched.append(
            {
                "rider_id": rider.get("id"),
                "coverage": rider.get("name"),
                "trigger_type": rider.get("trigger_type"),
                "coverage_kind": rider.get("coverage_kind"),
                "matched_reason": item["reason"],
                "estimated_amount": _estimate_from_rider(rider, understood),
                "amount_note": _amount_note(rider),
                "source": source
                or {
                    "page": rider.get("page"),
                    "article_no": rider.get("article_no"),
                    "text": _shorten(str(rider.get("raw_text") or "")),
                },
            }
        )

    return {
        "policy": {
            "policy_id": policy_res.data.get("id"),
            "name": policy_res.data.get("name"),
            "insurer": policy_res.data.get("insurer"),
            "type": policy_res.data.get("type"),
        },
        "coverage_candidates": enriched,
        "note": "공개/프리셋 약관 데이터 기반 후보입니다. 실제 지급 확정이 아니라 약관 확인용 분석입니다.",
    }


def _score_rider(rider: dict[str, object], situation: str, understood: dict[str, object]) -> dict[str, object]:
    text = " ".join(
        str(rider.get(key) or "")
        for key in ["name", "trigger_type", "trigger_detail", "unit_type", "unit_basis", "raw_text", "coverage_kind"]
    )
    disease_name = str(understood.get("disease_name") or "")
    admitted_days = understood.get("admitted_days")
    has_surgery = bool(understood.get("has_surgery"))
    is_injury = bool(understood.get("is_injury"))
    care_type = str(understood.get("care_type") or "")

    score = 0
    reasons = []

    if disease_name and disease_name in text:
        score += 4
        reasons.append(f"{disease_name} 단어가 담보/약관 문구에 포함됩니다.")
    if "암" in situation and "암" in text:
        score += 3
        reasons.append("암 관련 상황과 암 담보 단서가 맞습니다.")
    if is_injury and any(word in text for word in ["상해", "골절", "재해"]):
        score += 3
        reasons.append("상해/골절 관련 단서가 맞습니다.")
    if admitted_days is not None and "입원" in text:
        score += 3
        reasons.append("입원 상황과 입원 담보가 맞습니다.")
    if has_surgery and "수술" in text:
        score += 3
        reasons.append("수술 상황과 수술 담보가 맞습니다.")
    if care_type == "통원" and any(word in text for word in ["통원", "외래", "의료비", "실손"]):
        score += 2
        reasons.append("통원/진료 상황과 의료비 담보 단서가 맞습니다.")
    if any(word in situation for word in ["깁스", "기브스", "부목"]) and any(word in text for word in ["골절", "상해"]):
        score += 2
        reasons.append("깁스/부목 상황과 상해·골절 담보 단서가 맞습니다.")
    if any(word in situation for word in ["깁스", "기브스"]) and any(word in text for word in ["깁스", "기브스"]):
        score += 5
        reasons.append("깁스 치료 상황과 깁스 담보명이 직접 일치합니다.")
    if "부목" in situation and any(word in text for word in ["부목", "깁스", "기브스"]):
        score += 4
        reasons.append("부목/고정 치료 상황과 깁스·부목 담보 단서가 맞습니다.")
    if any(word in situation for word in ["꼬맸", "꿰맸", "봉합", "찢어", "베였"]) and any(
        word in text for word in ["상해", "창상", "봉합", "처치", "치료"]
    ):
        score += 4
        reasons.append("상처 봉합/처치 상황과 상해 치료 담보 단서가 맞습니다.")
    if any(word in situation for word in ["꼬맸", "꿰맸", "봉합"]) and any(word in text for word in ["봉합", "창상"]):
        score += 5
        reasons.append("봉합 상황과 창상봉합 담보명이 직접 일치합니다.")
    if not has_surgery and "수술" in text:
        score -= 2

    return {
        "rider": rider,
        "score": score,
        "reason": " ".join(reasons) if reasons else "직접 매칭 단서는 약하지만 같은 보험의 후보 담보입니다.",
    }


def _fetch_rider_source(db: Client, rider_id: str) -> dict[str, object] | None:
    res = db.table("rider_chunks").select("content,meta").eq("rider_id", rider_id).limit(1).execute()
    if not res.data:
        return None
    row = res.data[0]
    meta = row.get("meta") or {}
    return {
        "page": meta.get("page"),
        "article_no": meta.get("article_no"),
        "text": _shorten(row.get("content") or ""),
    }


def _estimate_from_rider(rider: dict[str, object], understood: dict[str, object]) -> int | None:
    unit_amount = rider.get("unit_amount")
    if not isinstance(unit_amount, int):
        return None

    admitted_days = understood.get("admitted_days")
    unit_type = str(rider.get("unit_type") or "")
    if isinstance(admitted_days, int) and "일" in unit_type:
        return unit_amount * admitted_days
    return unit_amount


def _amount_note(rider: dict[str, object]) -> str:
    if rider.get("unit_amount") is None:
        return "DB의 unit_amount가 비어 있어 가입금액/별표/보험증권 기준 확인이 필요합니다."
    return f"{rider.get('unit_type') or '담보'} 기준 단순 계산입니다."


def _understand_situation(situation: str) -> dict[str, object]:
    injury_part = _extract_injury_part(situation)
    return {
        "disease_name": _extract_disease_name(situation),
        "admitted_days": _extract_admitted_days(situation),
        "has_surgery": "수술" in situation,
        "is_injury": _is_injury_situation(situation),
        "injury_part": injury_part,
        "care_type": _infer_care_type(situation),
    }


def _policy_query_from_situation(situation: str, understood: dict[str, object]) -> str | None:
    disease_name = str(understood.get("disease_name") or "")
    if "암" in disease_name or "암" in situation:
        return "암"
    if understood.get("is_injury"):
        return "상해"
    if any(word in situation for word in ["실손", "통원", "진료비", "치료비", "병원", "진료"]):
        return "실손"
    if understood.get("admitted_days") is not None:
        return "질병"
    return None


def _select_mcp_policy_ids(situation: str, understood: dict[str, object]) -> list[str]:
    query = _policy_query_from_situation(situation, understood)
    policies = _fetch_public_policies(query=query, limit=3)
    if not policies and query:
        policies = _fetch_public_policies(query=None, limit=3)
    return [str(policy["policy_id"]) for policy in policies if policy.get("policy_id")]


def _build_mcp_dashboard_patch(
    situation: str,
    understood: dict[str, object],
    case_result: dict[str, object],
) -> dict[str, object]:
    care_type = understood.get("care_type")
    patch: dict[str, object] = {
        "policy_elapsed_days": 730,
        "surgery": bool(understood.get("has_surgery")),
        "annual_visit_count": 1,
    }

    if understood.get("is_injury"):
        disease_name = understood.get("disease_name") or case_result.get("disease_name")
        disease_kcd = _infer_mcp_kcd(situation, understood) or case_result.get("disease_kcd")
    else:
        disease_name = case_result.get("disease_name") or understood.get("disease_name")
        disease_kcd = case_result.get("disease_kcd") or _infer_mcp_kcd(situation, understood)
    if disease_name:
        patch["disease_name"] = disease_name
    if disease_kcd:
        patch["disease_kcd"] = disease_kcd

    admitted_days = understood.get("admitted_days")
    if care_type == "입원" or isinstance(admitted_days, int) and admitted_days > 0:
        patch["is_inpatient"] = True
        patch["is_outpatient"] = False
        patch["admission_days_current"] = admitted_days or 1
        patch["admission_days_diagnosed"] = admitted_days or 1
    else:
        patch["is_inpatient"] = False
        patch["is_outpatient"] = True
        patch["admission_days_current"] = 0
        patch["admission_days_diagnosed"] = 0

    treatment_items = _infer_treatment_items(situation)
    if treatment_items:
        patch["treatment_items"] = treatment_items

    payment_amount = _extract_payment_amount(situation)
    if payment_amount is not None:
        patch["payment_amount"] = payment_amount

    return patch


def _infer_mcp_kcd(situation: str, understood: dict[str, object]) -> str | None:
    disease_name = str(understood.get("disease_name") or "")
    if understood.get("is_injury"):
        if any(word in situation for word in ["골절", "부러졌", "깁스", "기브스"]):
            return "S62" if understood.get("injury_part") in ["손", "손목", "손가락"] else "S90"
        return "S60" if understood.get("injury_part") in ["손", "손목", "손가락"] else "T14"
    if "갑상선암" in disease_name or "갑상선암" in situation:
        return "C73"
    if "암" in disease_name or "암" in situation:
        return "C80"
    return None


def _infer_treatment_items(situation: str) -> list[str]:
    items = []
    if any(word in situation for word in ["깁스", "기브스", "캐스트"]):
        items.append("CAST")
    if any(word in situation for word in ["부목", "보조기"]):
        items.append("BRACE_SPLINT")
    if any(word in situation.lower() for word in ["xray", "x-ray"]) or "엑스레이" in situation:
        items.append("XRAY")
    if "주사" in situation:
        items.append("INJECTION")
    if any(word in situation for word in ["물리치료", "재활"]):
        items.append("PHYSICAL_THERAPY")
    if any(word in situation for word in ["도수", "충격파"]):
        items.append("MANUAL_THERAPY")
    if any(word in situation for word in ["꼬맸", "꿰맸", "봉합", "찢어", "베였"]):
        items.append("ETC:봉합")
    return list(dict.fromkeys(items))


def _extract_payment_amount(text: str) -> int | None:
    match = re.search(r"(\d+)\s*만\s*원", text)
    if match:
        return int(match.group(1)) * 10_000
    match = re.search(r"(\d{4,})\s*원", text)
    if match:
        return int(match.group(1))
    return None


def _summarize_search_results(results: list[dict[str, object]]) -> list[dict[str, object]]:
    visible_statuses = {"eligible", "potential", "conditional", "claimed", "boundary_not_met"}
    summarized = []
    for item in results:
        if item.get("status") not in visible_statuses:
            continue
        evidence = item.get("evidence") or {}
        summarized.append(
            {
                "policy": item.get("policy"),
                "coverage": item.get("rider"),
                "status": item.get("status"),
                "estimated_amount": item.get("estimated_amount"),
                "additional_amount": item.get("additional_amount"),
                "reduced_amount": item.get("reduced_amount"),
                "gap_days": item.get("gap_days"),
                "explanation": item.get("explanation"),
                "evidence": {
                    "article": evidence.get("article") if isinstance(evidence, dict) else None,
                    "page": evidence.get("page") if isinstance(evidence, dict) else None,
                    "excerpt": _shorten(evidence.get("quote") or "", 220) if isinstance(evidence, dict) else None,
                },
            }
        )
    return summarized[:8]


def _extract_injury_part(text: str) -> str | None:
    match = re.search(INJURY_PART_PATTERN, text)
    if match:
        return match.group(1)
    return None


def _is_injury_situation(text: str) -> bool:
    return any(word in text for word in INJURY_KEYWORDS)


def _infer_care_type(text: str) -> str | None:
    if "입원" in text:
        return "입원"
    if "수술" in text:
        return "수술"
    if any(
        word in text
        for word in ["통원", "외래", "병원", "진료", "치료", "꼬맸", "꿰맸", "봉합", "깁스", "기브스", "부목"]
    ):
        return "통원"
    return None


def _build_claim_dashboard(
    situation: str,
    understood: dict[str, object],
    analyses: list[dict[str, object]],
) -> dict[str, object]:
    coverages = _collect_possible_coverages(analyses)
    care_type = understood.get("care_type") or "확인 필요"

    return {
        "claim_summary": _claim_summary(situation, understood),
        "suspected_claim_type": care_type,
        "possible_coverages": coverages,
        "likely_documents": claim_documents(
            str(care_type) if care_type in ["입원", "수술", "통원", "진단"] else "통원"
        )["documents"],
        "missing_info": _missing_info(understood),
        "next_questions": _next_questions(understood),
        "caution": "공시실/프리셋 약관 기준 후보 분석입니다. 개인 가입 담보와 가입금액은 보험증권 또는 사용자 계약 데이터가 있어야 확정할 수 있습니다.",
    }


def _claim_summary(situation: str, understood: dict[str, object]) -> str:
    if understood.get("is_injury"):
        part = understood.get("injury_part") or "신체 부위"
        care = understood.get("care_type") or "치료"
        care_label = "통원 치료" if care == "통원" else str(care)
        return f"{part} 상해로 {care_label}를 받은 상황으로 보입니다."
    disease_name = understood.get("disease_name")
    if disease_name:
        return f"{disease_name} 관련 청구 상황으로 보입니다."
    return f"입력 상황: {situation}"


def _collect_possible_coverages(analyses: list[dict[str, object]]) -> list[dict[str, object]]:
    coverages = []
    seen = set()
    for analysis in analyses:
        policy = analysis.get("policy") or {}
        for candidate in analysis.get("coverage_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            coverage_key = (policy.get("name"), candidate.get("coverage"))
            if coverage_key in seen:
                continue
            seen.add(coverage_key)
            source = candidate.get("source") or {}
            coverages.append(
                {
                    "policy_name": policy.get("name"),
                    "insurer": policy.get("insurer"),
                    "coverage": candidate.get("coverage"),
                    "matched_reason": candidate.get("matched_reason"),
                    "estimated_amount": candidate.get("estimated_amount"),
                    "amount_note": candidate.get("amount_note"),
                    "evidence": {
                        "page": source.get("page") if isinstance(source, dict) else None,
                        "article_no": source.get("article_no") if isinstance(source, dict) else None,
                        "excerpt": source.get("text") if isinstance(source, dict) else None,
                    },
                }
            )
    return coverages[:5]


def _missing_info(understood: dict[str, object]) -> list[str]:
    missing = ["실제 가입한 보험/담보", "가입금액 또는 보장한도"]
    if understood.get("care_type") in [None, "통원"]:
        missing.append("진단명 또는 의사 소견")
    if understood.get("admitted_days") is None and understood.get("care_type") == "입원":
        missing.append("입원 일수")
    return missing


def _next_questions(understood: dict[str, object]) -> list[str]:
    questions = ["실제 가입한 보험 또는 분석할 policy_id가 있나요?"]
    if understood.get("is_injury"):
        questions.append("진단명이 염좌/골절/타박상 중 무엇으로 나왔나요?")
    if understood.get("care_type") == "통원":
        questions.append("통원 치료비 영수증과 진료비 세부내역서가 있나요?")
    return questions


def _shorten(text: str, limit: int = 260) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _supabase_error(code: str, exc: Exception) -> dict[str, object]:
    return {
        "error": code,
        "message": "Supabase 공개/프리셋 데이터 조회 중 오류가 발생했습니다.",
        "detail": str(exc),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
