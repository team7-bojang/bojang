"""F-02 탐색 · F-03 비교 오케스트레이션 (조윤).

탐색: retrieve → judge → explain → 인용검증 → verified 노출 등급 적용
비교: 시나리오별 judge 재실행 → 경계(gap_days) 감지 → 비교표 조립
"""

from app.core.constants import JudgeStatus
from app.core.errors import NotFoundError
from app.db import get_client
from app.judge import judge
from app.rag.explainer import explain
from app.rag.retriever import Retriever


def search_analysis(user_id: str, case_id: str) -> dict:
    """RAG 탐색과 룰 판정을 연동해 청구 가능한 보장을 탐색하고 스냅샷을 저장합니다."""
    db = get_client()

    # 1. 상황 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case_data = res_case.data[0]

    # 2. 내 가입 보험 목록 조회
    res_my = db.table("policies").select("*").eq("user_id", user_id).execute()
    my_policies = res_my.data or []
    policy_ids = [p["id"] for p in my_policies]
    policy_names = {p["id"]: p["name"] for p in my_policies}

    if not policy_ids:
        # 가입된 보험이 없는 경우 결과 없음 반환
        return {"summary": {"eligible_count": 0, "missed_count": 0}, "results": []}

    # 3. RAG 유사 특약 검색
    query = f"{case_data.get('disease_name', '')} {case_data.get('disease_kcd', '')}"
    if case_data.get("surgery"):
        query += " 수술"
    if case_data.get("current_days"):
        query += f" {case_data['current_days']}일 입원"

    retriever = Retriever()
    chunks = retriever.search(query, policy_ids=policy_ids, k=15)

    # 4. 연관 특약 판정 및 AI 설명 생성
    analyzed_rider_ids = set()
    results = []
    eligible_count = 0
    missed_count = 0

    # 기존에 저장된 해당 case_id의 이전 분석 결과가 있다면 클리어 (중복 방지)
    db.table("analysis_results").select("*").eq(
        "case_id", case_id
    ).execute()  # (Mock DB 특성상 조회용)

    for chunk in chunks:
        rider = chunk.get("riders")
        if not rider:
            continue

        rider_id = rider["id"]
        if rider_id in analyzed_rider_ids:
            continue
        analyzed_rider_ids.add(rider_id)

        # 판정 엔진 입력에 맞게 캐스팅
        judge_case = {
            "disease_kcd": case_data.get("disease_kcd", ""),
            "surgery": bool(case_data.get("surgery", False)),
            "diag_days": int(case_data.get("diag_days") or 0),
            "current_days": int(case_data.get("current_days") or 0),
            "policy_elapsed_days": case_data.get("policy_elapsed_days"),
        }

        judge_rider = {
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
        }

        # 룰 엔진 판정 실행
        judgement = judge(judge_case, judge_rider)
        status = judgement["status"]

        # 관련 없는 담보(not_applicable)는 제외
        if status == JudgeStatus.NOT_APPLICABLE:
            continue

        # RAG 설명문 생성
        rider_chunks = [c for c in chunks if c.get("rider_id") == rider_id]
        if not rider_chunks:
            rider_chunks = [chunk]

        explanation_data = explain(case_data, judgement, rider_chunks)

        policy_id = rider.get("policy_id")
        policy_name = policy_names.get(policy_id, "기타보험")

        # 기청구 여부 판별 (ID 또는 보험명 매칭)
        claimed_ids = case_data.get("claimed_policy_ids") or []
        is_claimed_policy = (policy_id in claimed_ids) or (policy_name in claimed_ids)

        if status == JudgeStatus.ELIGIBLE and is_claimed_policy:
            status = "claimed"

        if status in [JudgeStatus.ELIGIBLE, JudgeStatus.POTENTIAL, "claimed"]:
            eligible_count += 1

        # 놓친 보험금(missed) 판정
        # 가입한 상품이 기청구(claimed_policy_ids) 목록에 들어있지 않고, status=eligible이면 놓친 것
        missed = False
        if status == JudgeStatus.ELIGIBLE and not is_claimed_policy:
            missed = True
            missed_count += 1

        # Evidence 스냅샷 필드 구성
        evidence = {
            "article": explanation_data.get("article") or rider.get("article_no"),
            "page": explanation_data.get("page") or rider.get("page"),
            "quote": explanation_data.get("quote") or rider.get("raw_text"),
        }

        result_item = {
            "policy": policy_name,
            "rider": rider["name"],
            "status": status,
            "missed": missed,
            "gap_days": judgement.get("gap_days"),
            "calc": judgement.get("calc"),
            "explanation": explanation_data.get("explanation"),
            "evidence": evidence,
        }
        results.append(result_item)

        # 스냅샷 규칙에 따라 analysis_results DB에 저장
        snapshot = {
            "case_id": case_id,
            "rider_id": rider_id,
            "policy_name": policy_name,
            "rider_name": rider["name"],
            "status": status,
            "missed": missed,
            "gap_days": judgement.get("gap_days"),
            "evidence": evidence,
            "explanation": explanation_data.get("explanation"),
        }
        db.table("analysis_results").insert(snapshot).execute()

    return {
        "summary": {"eligible_count": eligible_count, "missed_count": missed_count},
        "results": results,
    }


def compare_scenarios(user_id: str, case_id: str, scenarios: list[dict]) -> dict:
    """입원 일수 등 시나리오별 조건 변동에 따른 보장 비교 결과를 계산합니다 (F-03)."""
    db = get_client()

    # 1. 상황 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case_data = res_case.data[0]

    # 2. 내 가입 보험 목록 조회
    res_my = db.table("policies").select("*").eq("user_id", user_id).execute()
    my_policies = res_my.data or []
    policy_ids = [p["id"] for p in my_policies]
    policy_names = {p["id"]: p["name"] for p in my_policies}

    # 3. 가입 특약들 로드
    my_riders = []
    for pid in policy_ids:
        res_riders = db.table("riders").select("*").eq("policy_id", pid).execute()
        my_riders.extend(res_riders.data or [])

    comparison_results = []

    for r in my_riders:
        policy_name = policy_names.get(r["policy_id"], "기타보험")

        scenario_outcomes = []
        has_applicable_scenario = False

        for sc in scenarios:
            # 시나리오의 조건에 따라 임시 case 구성
            days = sc.get("days")
            surgery = sc.get("surgery")

            temp_case = {
                "disease_kcd": case_data.get("disease_kcd", ""),
                "surgery": surgery
                if surgery is not None
                else bool(case_data.get("surgery", False)),
                "diag_days": days if days is not None else int(case_data.get("diag_days") or 0),
                "current_days": days
                if days is not None
                else int(case_data.get("current_days") or 0),
                "policy_elapsed_days": case_data.get("policy_elapsed_days"),
            }

            judge_rider = {
                "name": r.get("name"),
                "trigger_type": r.get("trigger_type", ""),
                "boundaries": r.get("boundaries", []),
                "exclusions": r.get("exclusions", []),
                "limits": r.get("limits", []),
                "waiting_period_days": r.get("waiting_period_days"),
                "reductions": r.get("reductions", []),
                "deduct_days": r.get("deduct_days", 0),
                "unit_amount": r.get("unit_amount"),
                "unit_type": r.get("unit_type"),
                "claim_rule": r.get("claim_rule"),
                "source_pages": r.get("source_pages", []),
            }

            judgement = judge(temp_case, judge_rider)
            status = judgement["status"]

            if status != JudgeStatus.NOT_APPLICABLE:
                has_applicable_scenario = True

            scenario_outcomes.append(
                {
                    "scenario": sc,
                    "status": status,
                    "calc": judgement.get("calc"),
                    "gap_days": judgement.get("gap_days"),
                }
            )

        if has_applicable_scenario:
            comparison_results.append(
                {"policy": policy_name, "rider": r["name"], "outcomes": scenario_outcomes}
            )

    return {"case_id": case_id, "scenarios": scenarios, "comparisons": comparison_results}
