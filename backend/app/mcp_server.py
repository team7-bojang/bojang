"""보장 서비스 MCP 서버.

마켓플레이스에 공급자 서버로 등록할 때 실행하는 독립 프로세스다.
Supabase의 공개/공시실 기반 프리셋 보험 데이터로 조회와 간단 분석 도구를 제공한다.
"""

from __future__ import annotations

import logging
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
if not os.getenv("BOJANG_MCP_DEMO_USER_ID"):
    raise RuntimeError("BOJANG_MCP_DEMO_USER_ID 환경변수가 없습니다. (MCP 데모 사용자 식별용 필수값)")
MCP_DEMO_USER_ID = os.environ["BOJANG_MCP_DEMO_USER_ID"]
MCP_DEMO_ELAPSED_DAYS = int(os.getenv("BOJANG_MCP_DEMO_ELAPSED_DAYS", "730"))
logger = logging.getLogger(__name__)
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
    builder = db.table("policies").select("id,name,insurer,type,is_preset").eq("is_preset", True)

    normalized = re.sub(r"[,()%]", "", query.replace("보험", "")).strip() if query else ""
    if normalized:
        pattern = f"%{normalized}%"
        builder = builder.or_(f"name.ilike.{pattern},insurer.ilike.{pattern},type.ilike.{pattern}")

    res = builder.limit(limit).execute()
    rows = res.data or []

    return [
        {
            "policy_id": row.get("id"),
            "name": row.get("name"),
            "insurer": row.get("insurer"),
            "type": row.get("type"),
        }
        for row in rows
    ]


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
        "policy_elapsed_days": MCP_DEMO_ELAPSED_DAYS,
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


def _shorten(text: str, limit: int = 260) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _supabase_error(code: str, exc: Exception) -> dict[str, object]:
    logger.exception("Supabase 공개/프리셋 데이터 조회 실패: %s", code, exc_info=exc)
    return {
        "error": code,
        "message": "Supabase 공개/프리셋 데이터 조회 중 오류가 발생했습니다.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
