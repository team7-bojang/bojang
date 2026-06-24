"""리포트·체크리스트 생성 (F-04) — 서류 룰 매핑 + 스냅샷 저장."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.core.errors import NotFoundError
from app.db import get_client
from app.judge import judge
from app.rag.explainer import explain
from app.services.analysis_service import (
    get_disease_groups_for_kcd,
    get_disease_rules_for_rider,
    get_rider_treatment_codes,
)


def create_report(user_id: str, case_id: str) -> dict:
    """분석 결과를 가공하여 종합 분석 리포트를 생성하고 저장합니다 (F-04)."""
    db = get_client()

    # 1. Case 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case = res_case.data[0]

    # 2. 분석 결과 조회
    res_analysis = db.table("analysis_results").select("*").eq("case_id", case_id).execute()
    analysis_data = res_analysis.data or []

    # 2-1. 지급 후보 특약에 대한 AI 설명(LLM) 동적 지연 생성 (2단계화 적용)
    candidate_results = [r for r in analysis_data if r.get("status") in ["eligible", "potential", "claimed"]]

    def explain_candidate(result_row):
        rider_id = result_row.get("rider_id")
        if not rider_id:
            return result_row

        # 스레드 안전성을 위해 스레드 개별 Supabase 클라이언트 생성
        thread_db = get_client()

        res_rider = thread_db.table("riders").select("*").eq("id", rider_id).execute()
        if not res_rider.data:
            return result_row
        rider = res_rider.data[0]

        req_groups, excl_groups = get_disease_rules_for_rider(
            thread_db, rider_id, rider.get("name") or "", rider.get("trigger_type")
        )

        judge_case = {
            "disease_kcd": case.get("disease_kcd", ""),
            "disease_name": case.get("disease_name", ""),
            "surgery": bool(case.get("surgery", False)),
            "diag_days": int(case.get("admission_days_diagnosed") or case.get("diag_days") or 0),
            "current_days": int(case.get("admission_days_current") or case.get("current_days") or 0),
            "policy_elapsed_days": case.get("policy_elapsed_days"),
            "treatment_items": case.get("treatment_items") or [],
            "disease_groups": get_disease_groups_for_kcd(thread_db, case.get("disease_kcd")),
            "treatment_codes": case.get("treatment_items") or [],
            "coverage_amounts": case.get("coverage_amounts"),
            "covered_amounts": case.get("covered_amounts"),
            "payment_amount": case.get("payment_amount"),
        }

        judge_rider = {
            "id": rider_id,
            "name": rider.get("name"),
            "trigger_type": rider.get("trigger_type", ""),
            "boundaries": rider.get("boundaries", []),
            "exclusions": rider.get("exclusions", []),
            "limits": rider.get("limits", []),
            "waiting_period_days": rider.get("waiting_period_days"),
            "reductions": rider.get("reductions", []),
            "deduct_days": rider.get("deduct_days", 0),
            "unit_amount": rider.get("unit_amount"),
            "unit_type": rider.get("unit_type"),
            "claim_rule": rider.get("claim_rule"),
            "source_pages": rider.get("source_pages", []),
            "require_groups": req_groups,
            "exclude_groups": excl_groups,
            "require_treatments": get_rider_treatment_codes(thread_db, rider_id, rider.get("name")),
            "treatment_codes": get_rider_treatment_codes(thread_db, rider_id, rider.get("name")),
        }

        judgement = judge(judge_case, judge_rider)

        rider_chunks = [
            {
                "rider_id": rider_id,
                "content": rider.get("raw_text") or "",
                "meta": {
                    "page": rider.get("page"),
                    "article_no": rider.get("article_no"),
                    "waiting_period_days": rider.get("waiting_period_days"),
                },
            }
        ]

        try:
            explanation_data = explain(case, judgement, rider_chunks)
            evidence = {
                "article": explanation_data.get("article") or rider.get("article_no"),
                "page": explanation_data.get("page") or rider.get("page"),
                "quote": explanation_data.get("quote") or rider.get("raw_text"),
            }
            result_row["explanation"] = explanation_data.get("explanation")
            result_row["evidence"] = evidence

            # analysis_results 테이블에도 AI 설명문 최신화 업데이트
            thread_db.table("analysis_results").update(
                {"explanation": explanation_data.get("explanation"), "evidence": evidence}
            ).eq("id", result_row["id"]).execute()

        except Exception as e:
            print(f"[report_service] Delayed AI explanation failed for {rider_id}: {e}")

        return result_row

    if candidate_results:
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(explain_candidate, candidate_results))

    # 3. 리포트 본문 조립
    eligible_covers = []
    missed_covers = []

    for r in analysis_data:
        cover_info = {
            "policy": r.get("policy_name"),
            "rider": r.get("rider_name"),
            "status": r.get("status"),
            "explanation": r.get("explanation"),
            "evidence": r.get("evidence"),
        }
        if r.get("status") in ["eligible", "potential", "claimed"]:
            eligible_covers.append(cover_info)
            if r.get("missed"):
                missed_covers.append(cover_info)

    # 질환별 맞춤 체크리스트 작성
    disease_name = case.get("disease_name", "")
    checklist = [
        {"task": "치료 병원에서 '진료비 세부산정내역서' 발급 받기", "done": False},
        {"task": "병원비 결제 카드 영수증 챙기기", "done": False},
    ]
    if "뇌" in disease_name or "암" in disease_name:
        checklist.append(
            {
                "task": ("전문의 진단명이 기재된 '진단서' 및 '조직검사결과지' 또는 '영상판독서' 챙기기"),
                "done": False,
            }
        )
    if case.get("surgery"):
        checklist.append(
            {
                "task": ("수술 일자 및 수술명 정보가 포함된 '수술확인서' 또는 '진단서' 발급 받기"),
                "done": False,
            }
        )
    admission_days_current = case.get("admission_days_current", case.get("current_days"))
    if admission_days_current and admission_days_current > 0:
        checklist.append({"task": "입원 기간이 명시된 '입퇴원확인서' 챙기기", "done": False})

    # 소멸시효 문구
    statute_txt = (
        "상법 제662조에 따라 보험금 청구권은 사고 발생일"
        "(진단일, 수술일, 퇴원일 등)로부터 3년 간 행사하지 않으면 시효로 소멸합니다."
    )

    # 면책 고지
    disclaimer_txt = (
        "본 분석 결과는 약관 원문 및 기입해주신 치료 상황을 바탕으로 "
        "AI가 자동 산출한 참고 자료입니다. 실제 보험금 지급 여부 및 "
        "상세 보장액은 보험사의 심사 결과에 따라 달라질 수 있습니다."
    )

    report_id = str(uuid.uuid4())
    report_body = {
        "summary": {
            "disease_kcd": case.get("disease_kcd"),
            "disease_name": case.get("disease_name"),
            "surgery": case.get("surgery"),
            "admission_days_current": admission_days_current,
        },
        "eligible_covers": eligible_covers,
        "missed_covers": missed_covers,
        "checklist": checklist,
        "statute_of_limitations": statute_txt,
        "disclaimer": disclaimer_txt,
        "created_at": datetime.now(UTC).isoformat(),
    }

    report_data = {
        "id": report_id,
        "case_id": case_id,
        "user_id": user_id,
        "body": report_body,
        "created_at": datetime.now(UTC).isoformat(),
    }

    db.table("reports").insert(report_data).execute()

    return {"report_id": report_id}


def get_report(report_id: str) -> dict:
    """저장된 종합 분석 리포트를 조회합니다 (SCR-06)."""
    db = get_client()

    res = db.table("reports").select("*").eq("id", report_id).execute()
    if not res.data:
        raise NotFoundError("해당 리포트를 찾을 수 없습니다.")

    report = res.data[0]
    return {"report_id": report["id"], "body": report["body"]}
