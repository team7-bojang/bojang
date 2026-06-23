"""F-02 탐색 · F-03 비교 오케스트레이션 (조윤).

탐색: retrieve → judge → explain → 인용검증 → verified 노출 등급 적용
비교: 시나리오별 judge 재실행 → 경계(gap_days) 감지 → 비교표 조립
"""

from app.core.constants import JudgeStatus
from app.core.errors import ForbiddenError, NotFoundError
from app.db import get_client
from app.judge import judge
from app.rag.explainer import explain
from app.rag.retriever import Retriever

# 데모 및 테스트용 임의 보험/특약 데이터 정의 (DB 데이터가 없을 때 폴백으로 사용)
DUMMY_POLICIES = [
    {
        "id": "dummy-policy-db-3dae",
        "name": "무배당 프로미라이프 계속받는 3대질병보장보험",
        "insurer": "DB손해보험",
        "type": "질병",
        "user_id": "dummy-user",
    },
    {
        "id": "dummy-policy-meritz-silson",
        "name": "메리츠 무배당 실손의료비보험",
        "insurer": "메리츠화재",
        "type": "실손",
        "user_id": "dummy-user",
    },
]

DUMMY_RIDERS = [
    {
        "id": "dummy-rider-db-hosp",
        "policy_id": "dummy-policy-db-3dae",
        "name": "질병입원일당(1일이상180일한도)",
        "trigger_type": "입원",
        "verified": True,
        "is_main": False,
        "coverage_kind": "정액",
        "unit_amount": 10000,
        "unit_type": "1일당",
        "boundaries": [{"condition_days": 1, "effect": "1일 이상 입원 시 첫날부터 지급"}],
        "deduct_days": 0,
        "limits": [{"scope": "per_hospitalization", "unit": "days", "value": 180}],
        "waiting_period_days": 0,
        "reductions": [],
        "exclusions": [],
        "claim_rule": None,
        "article_no": "제12조",
        "page": 45,
        "raw_text": (
            "피보험자가 질병으로 인하여 1일 이상 입원하여 치료를 받은 경우 "
            "첫날부터 입원 1일당 가입금액을 지급합니다. (180일 한도)"
        ),
    },
    {
        "id": "dummy-rider-db-stroke",
        "policy_id": "dummy-policy-db-3dae",
        "name": "뇌졸중진단비",
        "trigger_type": "진단",
        "verified": True,
        "is_main": False,
        "coverage_kind": "정액",
        "unit_amount": 20000000,
        "unit_type": "일시금",
        "boundaries": [
            {
                "condition_days": 0,
                "effect": "뇌졸중(KCD I60~I63, I65, I66) 진단 확정 시 지급",
            }
        ],
        "deduct_days": 0,
        "limits": [],
        "waiting_period_days": 90,
        "reductions": [{"elapsed_days": 365, "ratio": 0.5}],
        "exclusions": [],
        "claim_rule": None,
        "article_no": "제15조",
        "page": 60,
        "raw_text": (
            "피보험자가 최초로 뇌졸중으로 진단 확정되었을 때에는 뇌졸중 진단비를 "
            "지급합니다. 단, 계약일로부터 1년 미만인 경우 50%를 감액하여 지급합니다."
        ),
    },
    {
        "id": "dummy-rider-meritz-hosp",
        "policy_id": "dummy-policy-meritz-silson",
        "name": "질병급여실손의료비(갱신형)-입원",
        "trigger_type": "입원",
        "verified": True,
        "is_main": False,
        "coverage_kind": "실손",
        "unit_amount": 50000000,
        "unit_type": "일시금",
        "boundaries": [],
        "deduct_days": 0,
        "limits": [],
        "waiting_period_days": 0,
        "reductions": [],
        "exclusions": [],
        "claim_rule": {
            "formula": "min(50000000, actual_cost * 0.8)",
            "copay_ratio": 0.2,
            "deductible": {"type": "fixed", "value": 0},
        },
        "article_no": "제3조",
        "page": 12,
        "raw_text": (
            "피보험자가 질병으로 인하여 입원하여 치료를 받은 경우 국민건강보험법에서 "
            "정한 요양급여 중 본인부담금의 80% 상당액을 보상합니다. (5천만원 한도)"
        ),
    },
]

DUMMY_CHUNKS = [
    {
        "rider_id": r["id"],
        "raw_text": r["raw_text"],
        "page": r["page"],
        "riders": r,
    }
    for r in DUMMY_RIDERS
]


_disease_group_code_rules_cache = None
_rider_disease_rules_cache = None


def get_disease_groups_for_kcd(db, kcd: str | None) -> list[str]:
    global _disease_group_code_rules_cache
    if not kcd:
        return []
    try:
        if _disease_group_code_rules_cache is None:
            rules_res = db.table("disease_group_code_rules").select("*").execute()
            _disease_group_code_rules_cache = rules_res.data or []

        rules_data = _disease_group_code_rules_cache
        matched_group_ids = []
        excluded_group_ids = []
        kcd_clean = kcd[:3].upper()
        for rule in rules_data:
            start = rule.get("code_start")
            end = rule.get("code_end")
            group_id = rule.get("group_id")

            in_range = False
            if start:
                start = start.upper()
                if end:
                    end = end.upper()
                    if start <= kcd_clean <= end:
                        in_range = True
                else:
                    if kcd.upper().startswith(start):
                        in_range = True

            if in_range:
                if rule.get("rule_type") == "include":
                    matched_group_ids.append(group_id)
                elif rule.get("rule_type") == "exclude":
                    excluded_group_ids.append(group_id)

        return [gid for gid in matched_group_ids if gid not in excluded_group_ids]
    except Exception as e:
        print(f"[AnalysisService] Failed to query disease groups for {kcd}: {e}")
        return []


def get_disease_rules_for_rider(
    db, rider_id: str, rider_name: str, trigger_type: str | None
) -> tuple[list[str], list[str]]:
    global _rider_disease_rules_cache
    require_groups = []
    exclude_groups = []
    try:
        if _rider_disease_rules_cache is None:
            res = db.table("rider_disease_rules").select("*").execute()
            _rider_disease_rules_cache = res.data or []

        rules = _rider_disease_rules_cache

        specific_rules = [r for r in rules if r.get("rider_id") == rider_id]

        matched_rules = []
        if specific_rules:
            matched_rules = specific_rules
        else:
            for r in rules:
                if r.get("rider_id") is None and r.get("rider_name_pattern"):
                    pattern = r["rider_name_pattern"].replace("%", "")
                    if pattern in rider_name:
                        req_trigger = r.get("require_trigger_type")
                        if req_trigger and req_trigger != trigger_type:
                            continue
                        matched_rules.append(r)

        for r in matched_rules:
            gid = r.get("group_id")
            rtype = r.get("rule_type")
            if not gid:
                continue
            if rtype == "required":
                require_groups.append(gid)
            elif rtype == "excluded":
                exclude_groups.append(gid)

        return list(set(require_groups)), list(set(exclude_groups))
    except Exception as e:
        print(f"[AnalysisService] Failed to query rider disease rules for {rider_name}: {e}")
        return [], []


def get_rider_treatment_codes(db, rider_id: str, rider_name: str) -> list[str]:
    """해당 특약에 지정된 치료 종류 코드 목록을 조회합니다 (실제 DB 조회 + 특약명 폴백)."""
    try:
        res = db.table("rider_treatment_rules").select("treatment_code").eq("rider_id", rider_id).execute()
        if res.data:
            return [row.get("treatment_code") for row in res.data if row.get("treatment_code")]
    except Exception as e:
        print(f"[AnalysisService] Failed to query rider_treatment_rules for {rider_id}: {e}")

    # DB 조회 실패 또는 비어있을 시 특약명을 기반으로 하드코딩 폴백 매핑
    codes = []
    rider_name_lower = (rider_name or "").lower()

    if any(w in rider_name_lower for w in ["도수", "충격파", "증식"]):
        codes.append("MANUAL_THERAPY")
    if "물리" in rider_name_lower:
        codes.append("PHYSICAL_THERAPY")
    if "mri" in rider_name_lower or "mra" in rider_name_lower:
        codes.append("MRI_MRA")
    if any(w in rider_name_lower for w in ["엑스레이", "x-ray", "xray"]):
        codes.append("XRAY")
    if "주사" in rider_name_lower:
        codes.append("INJECTION")
    if "응급" in rider_name_lower:
        codes.append("EMERGENCY")
    if "깁스" in rider_name_lower:
        codes.append("CAST")

    return codes


def search_analysis(user_id: str, case_id: str) -> dict:
    """RAG 탐색과 룰 판정을 연동해 청구 가능한 보장을 탐색하고 스냅샷을 저장합니다."""
    db = get_client()

    # 1. 상황 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case_data = res_case.data[0]
    if case_data.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")

    # 2. 내 가입 보험 목록 조회 (cases.policy_ids 기반 조회)
    case_policy_ids = case_data.get("policy_ids") or []
    my_policies = []
    if case_policy_ids:
        res_my = db.table("policies").select("*").in_("id", case_policy_ids).execute()
        my_policies = res_my.data or []

    notice = None
    is_dummy_used = False

    if not my_policies:
        try:
            res_preset = db.table("policies").select("*").eq("is_preset", True).limit(2).execute()
            my_policies = res_preset.data or []
            if my_policies:
                notice = "실제 등록한 보험이 없어, 시스템에 등록된 대표 프리셋 보험 정보를 기반으로 청구 분석을 수행했습니다."
        except Exception as e:
            print(f"[analysis_service] Failed to fetch preset policies: {e}")

        if not my_policies:
            my_policies = []
            notice = "분석 가능한 가입 보험 정보가 존재하지 않습니다."

    policy_ids = [p["id"] for p in my_policies]
    policy_names = {p["id"]: p["name"] for p in my_policies}

    # 3. RAG 유사 특약 검색
    query = f"{case_data.get('disease_name', '')} {case_data.get('disease_kcd', '')}"
    if case_data.get("surgery"):
        query += " 수술"
    admission_days_current = case_data.get("admission_days_current", case_data.get("current_days"))
    if admission_days_current:
        query += f" {admission_days_current}일 입원"

    treatment_mapping = {
        "MANUAL_THERAPY": "도수치료 체외충격파 증식치료",
        "PHYSICAL_THERAPY": "물리치료",
        "MRI_MRA": "MRI MRA 자기공명영상",
        "XRAY": "엑스레이 X-ray",
        "INJECTION": "주사",
        "EMERGENCY": "응급실",
        "CAST": "깁스 깁스치료",
    }
    treatment_items = case_data.get("treatment_items") or []
    for item in treatment_items:
        kw = treatment_mapping.get(item)
        if kw:
            query += f" {kw}"

    retriever = Retriever()
    chunks = []

    if not is_dummy_used:
        try:
            chunks = retriever.search(query, policy_ids=policy_ids, disease_kcd=case_data.get("disease_kcd"), k=15)
        except Exception as e:
            print(f"[analysis_service] RAG retriever.search failed: {e}")
            chunks = []

        # RAG 검색 결과에 누락된 rider가 있을 수 있으므로,
        # policy_ids에 속한 모든 rider를 DB에서 직접 로드하여 보강
        rag_rider_ids = {c.get("riders", {}).get("id") for c in chunks if c.get("riders")}
        for pid in policy_ids:
            try:
                res_r = db.table("riders").select("*").eq("policy_id", pid).execute()
                for r in res_r.data or []:
                    if r["id"] not in rag_rider_ids:
                        chunks.append({"rider_id": r["id"], "riders": r, "content": r.get("raw_text") or ""})
                        rag_rider_ids.add(r["id"])
            except Exception as e:
                print(f"[analysis_service] Failed to load riders for {pid}: {e}")

    if not chunks:
        if not notice:
            notice = "가입한 보험의 세부 약관 및 특약 정보가 DB에 등록되어 있지 않아 분석이 제한됩니다."

    # 4. 연관 특약 판정 및 AI 설명 생성
    analyzed_rider_ids = set()
    results = []
    eligible_count = 0
    missed_count = 0

    for chunk in chunks:
        rider = chunk.get("riders")
        if not rider:
            continue

        rider_id = rider["id"]
        if rider_id in analyzed_rider_ids:
            continue
        analyzed_rider_ids.add(rider_id)

        # 질병군 및 특약 매칭 규칙 조회
        req_groups, excl_groups = get_disease_rules_for_rider(
            db, rider_id, rider.get("name") or "", rider.get("trigger_type")
        )

        # 판정 엔진 입력에 맞게 캐스팅
        judge_case = {
            "disease_kcd": case_data.get("disease_kcd", ""),
            "disease_name": case_data.get("disease_name", ""),
            "surgery": bool(case_data.get("surgery", False)),
            "diag_days": int(case_data.get("admission_days_diagnosed") or case_data.get("diag_days") or 0),
            "current_days": int(case_data.get("admission_days_current") or case_data.get("current_days") or 0),
            "policy_elapsed_days": case_data.get("policy_elapsed_days"),
            "treatment_items": case_data.get("treatment_items") or [],
            "disease_groups": get_disease_groups_for_kcd(db, case_data.get("disease_kcd")),
            "treatment_codes": case_data.get("treatment_items") or [],
            "coverage_amounts": case_data.get("coverage_amounts"),
            "covered_amounts": case_data.get("covered_amounts"),
            "payment_amount": case_data.get("payment_amount"),
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
            "require_treatments": get_rider_treatment_codes(db, rider_id, rider.get("name")),
            "treatment_codes": get_rider_treatment_codes(db, rider_id, rider.get("name")),
        }

        # 룰 엔진 판정 실행
        judgement = judge(judge_case, judge_rider)
        status = judgement["status"]

        # RAG 설명문 생성
        rider_chunks = [c for c in chunks if c.get("rider_id") == rider_id]
        if not rider_chunks:
            rider_chunks = [chunk]

        import os

        if status == JudgeStatus.NOT_APPLICABLE:
            explanation_data = {
                "explanation": judgement.get("reason") or f"지급 상태가 [{status}]로 판정되었습니다.",
                "article": rider.get("article_no"),
                "page": rider.get("page"),
                "quote": rider.get("raw_text"),
            }
        elif os.environ.get("MOCK_LLM") == "True":
            explanation_data = {
                "explanation": (
                    f"약관 {rider.get('article_no', '조항')}에 근거하여 지급 상태가 [{status}]로 판정되었습니다."
                ),
                "article": rider.get("article_no"),
                "page": rider.get("page"),
                "quote": rider.get("raw_text"),
            }
        else:
            try:
                explanation_data = explain(case_data, judgement, rider_chunks)
            except Exception as e:
                print(f"[analysis_service] AI explanation failed: {e}")
                explanation_data = {
                    "explanation": (
                        f"약관 {rider.get('article_no', '조항')}에 근거하여 지급 상태가 [{status}]로 판정되었습니다."
                    ),
                    "article": rider.get("article_no"),
                    "page": rider.get("page"),
                    "quote": rider.get("raw_text"),
                }

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
            "payable_days": judgement.get("payable_days"),
            "estimated_amount": judgement.get("expected_amount") or 0,
            "reduction": judgement.get("reduction"),
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
            "status": status[:20] if status else None,
            "missed": missed,
            "gap_days": judgement.get("gap_days"),
            "evidence": evidence,
            "explanation": explanation_data.get("explanation"),
        }
        try:
            db.table("analysis_results").insert(snapshot).execute()
        except Exception as db_err:
            print(f"[analysis_service] Snapshot save failed: {db_err}")

    return {
        "summary": {"eligible_count": eligible_count, "missed_count": missed_count},
        "results": results,
        "notice": notice,
    }


def compare_scenarios(
    user_id: str,
    case_id: str,
    scenarios_input: list[dict] = None,
    current_days: int = None,
    target_days: int = None,
) -> dict:
    """입원 경과일수를 기준으로 보장 조건 차이를 비교합니다 (v2.1).

    scenarios_input이 전달되면 프론트엔드 맞춤형 다중 시나리오 비교 결과({scenarios, comparisons})를 반환하고,
    기존처럼 current_days와 target_days가 전달되면 기존 포맷의 비교 결과({comparison, slider, ...})를 반환합니다.
    """
    db = get_client()

    # 1. 상황 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case_data = res_case.data[0]
    if case_data.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")

    # 2. 내 가입 보험 목록 조회 (cases.policy_ids 기반 조회)
    case_policy_ids = case_data.get("policy_ids") or []
    my_policies = []
    if case_policy_ids:
        res_my = db.table("policies").select("*").in_("id", case_policy_ids).execute()
        my_policies = res_my.data or []

    notice = None
    is_dummy_used = False

    if not my_policies:
        try:
            res_preset = db.table("policies").select("*").eq("is_preset", True).limit(2).execute()
            my_policies = res_preset.data or []
            if my_policies and not scenarios_input:
                notice = "실제 등록한 보험이 없어, 시스템에 등록된 대표 프리셋 보험 정보를 기반으로 퇴원 시점 비교표를 구성했습니다."
        except Exception as e:
            print(f"[analysis_service] Failed to fetch preset policies for compare: {e}")

        if not my_policies:
            my_policies = []
            if not scenarios_input:
                notice = "비교 분석을 위한 가입 보험 정보가 존재하지 않습니다."

    policy_ids = [p["id"] for p in my_policies]
    policy_names = {p["id"]: p["name"] for p in my_policies}
    policy_insurers = {p["id"]: p["insurer"] for p in my_policies}

    # 3. 가입 특약들 로드
    my_riders = []
    if not is_dummy_used:
        for pid in policy_ids:
            try:
                res_riders = db.table("riders").select("*").eq("policy_id", pid).execute()
                my_riders.extend(res_riders.data or [])
            except Exception as e:
                print(f"[analysis_service] Fetch riders failed for {pid}: {e}")

    if not my_riders:
        if not scenarios_input and not notice:
            notice = "비교 분석에 필요한 입원 특약 정보가 가입 보험 약관 DB에 존재하지 않습니다."

    # ─── 분기 1: 신규 다중 시나리오 방식 (scenarios_input이 전달된 경우) ───
    if scenarios_input is not None:
        comparisons = []
        for r in my_riders:
            trigger = r.get("trigger_type")
            policy_id = r.get("policy_id")
            policy_name = policy_names.get(policy_id, "기타보험")

            outcomes = []
            for sc in scenarios_input:
                days = sc.get("days", 0)

                # 질병군 및 특약 매칭 규칙 조회
                req_groups, excl_groups = get_disease_rules_for_rider(
                    db, r.get("id"), r.get("name") or "", r.get("trigger_type")
                )

                # 입원 특약은 시나리오 일수(days)로 판정, 그 외는 case의 기본 일수로 판정
                actual_days = days if trigger == "입원" else (case_data.get("admission_days_current") or 1)

                temp_case = {
                    "disease_kcd": case_data.get("disease_kcd", ""),
                    "disease_name": case_data.get("disease_name", ""),
                    "surgery": bool(case_data.get("surgery", False)),
                    "diag_days": actual_days,
                    "current_days": actual_days,
                    "policy_elapsed_days": case_data.get("policy_elapsed_days"),
                    "disease_groups": get_disease_groups_for_kcd(db, case_data.get("disease_kcd")),
                    "treatment_codes": case_data.get("treatment_items") or [],
                    "coverage_amounts": case_data.get("coverage_amounts"),
                    "covered_amounts": case_data.get("covered_amounts"),
                    "payment_amount": case_data.get("payment_amount"),
                }

                judge_rider = {
                    "id": r.get("id"),
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
                    "require_groups": req_groups,
                    "exclude_groups": excl_groups,
                    "require_treatments": get_rider_treatment_codes(db, r.get("id"), r.get("name")),
                    "treatment_codes": get_rider_treatment_codes(db, r.get("id"), r.get("name")),
                }

                judgement = judge(temp_case, judge_rider)
                status = judgement["status"]
                gap_days = judgement.get("gap_days")

                calc_text = None
                if status == JudgeStatus.BOUNDARY_NOT_MET:
                    matched_b = judgement.get("matched_boundary") or "조건"
                    calc_text = f"{matched_b} 조건 미달"
                elif status == JudgeStatus.ELIGIBLE:
                    calc_text = judgement.get("calc")
                    if not calc_text:
                        unit_amount = r.get("unit_amount") or 10000
                        deduct_days = r.get("deduct_days") or 0
                        effective_days = max(0, actual_days - deduct_days)
                        if trigger == "입원":
                            if deduct_days > 0:
                                calc_text = f"{deduct_days + 1}일째부터 지급, {effective_days}일 지급 ({unit_amount * effective_days:,}원)"
                            else:
                                calc_text = f"{effective_days}일 지급 ({unit_amount * effective_days:,}원)"
                        else:
                            calc_text = f"{unit_amount:,}원 지급"

                outcomes.append(
                    {
                        "status": status.value if hasattr(status, "value") else str(status),
                        "calc": calc_text,
                        "gap_days": gap_days,
                    }
                )

            comparisons.append({"policy": policy_name, "rider": r["name"], "outcomes": outcomes})

        scenarios_output = [{"name": sc.get("name", "")} for sc in scenarios_input]
        return {"scenarios": scenarios_output, "comparisons": comparisons}

    # ─── 분기 2: 기존 단일/이중 일수 비교 방식 (current_days, target_days가 전달된 경우) ───
    if current_days is None:
        current_days = case_data.get("admission_days_current") or 1
    if target_days is None:
        target_days = current_days

    comparison_results = []
    all_breakpoints = set()
    has_special_coverage = False
    slider_max = 28

    for r in my_riders:
        trigger = r.get("trigger_type")
        policy_id = r.get("policy_id")
        policy_name = policy_names.get(policy_id, "기타보험")
        insurer = policy_insurers.get(policy_id, "기타보험사")

        boundaries = r.get("boundaries") or []
        is_special = False

        for b in boundaries:
            cond_days = b.get("condition_days", 0)
            if cond_days > 1:
                all_breakpoints.add(cond_days)
                is_special = True
                if cond_days > slider_max:
                    slider_max = cond_days

        scenarios = []
        if trigger == "입원":
            if current_days == target_days:
                scenario_days_list = [None]
            else:
                scenario_days_list = [current_days, target_days]
        else:
            scenario_days_list = [None]

        for days in scenario_days_list:
            req_groups, excl_groups = get_disease_rules_for_rider(
                db, r.get("id"), r.get("name") or "", r.get("trigger_type")
            )
            actual_days = days if days is not None else current_days

            temp_case = {
                "disease_kcd": case_data.get("disease_kcd", ""),
                "disease_name": case_data.get("disease_name", ""),
                "surgery": bool(case_data.get("surgery", False)),
                "diag_days": actual_days,
                "current_days": actual_days,
                "policy_elapsed_days": case_data.get("policy_elapsed_days"),
                "disease_groups": get_disease_groups_for_kcd(db, case_data.get("disease_kcd")),
                "treatment_codes": case_data.get("treatment_items") or [],
                "coverage_amounts": case_data.get("coverage_amounts"),
                "covered_amounts": case_data.get("covered_amounts"),
                "payment_amount": case_data.get("payment_amount"),
            }

            judge_rider = {
                "id": r.get("id"),
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
                "require_groups": req_groups,
                "exclude_groups": excl_groups,
                "require_treatments": get_rider_treatment_codes(db, r.get("id"), r.get("name")),
                "treatment_codes": get_rider_treatment_codes(db, r.get("id"), r.get("name")),
            }

            judgement = judge(temp_case, judge_rider)
            status = judgement["status"]

            calc_text = None
            amount_note = None
            gap_days = judgement.get("gap_days")

            if status == JudgeStatus.BOUNDARY_NOT_MET:
                matched_b = judgement.get("matched_boundary") or "조건"
                calc_text = f"{matched_b} 조건 미달 (gap_days: {gap_days})"
            elif status == JudgeStatus.ELIGIBLE:
                unit_amount = r.get("unit_amount") or 10000
                deduct_days = r.get("deduct_days") or 0
                effective_days = max(0, actual_days - deduct_days)

                calc_text = judgement.get("calc")
                if not calc_text:
                    if trigger == "입원":
                        if deduct_days > 0:
                            calc_text = (
                                f"{deduct_days + 1}일째부터 지급, {effective_days}일 지급 (deduct_days: {deduct_days})"
                            )
                        else:
                            calc_text = f"{effective_days}일 지급"
                    else:
                        calc_text = f"{unit_amount:,}원 지급"

                if "일시금" in (r.get("unit_type") or "") or "정액" in (r.get("unit_basis") or ""):
                    amount_note = f"{unit_amount:,}원"
                elif trigger == "입원":
                    amount_note = f"{unit_amount * effective_days:,}원"
                else:
                    amount_note = f"{unit_amount:,}원"

            scenarios.append(
                {
                    "days": days,
                    "status": status.value if hasattr(status, "value") else str(status),
                    "type": "special" if is_special else "base",
                    "label": "특약 조건" if is_special else ("입원일당" if trigger == "입원" else "진단/수술"),
                    "calc": calc_text,
                    "amount_note": amount_note,
                    "gap_days": gap_days,
                    "payable_days": judgement.get("payable_days"),
                    "estimated_amount": judgement.get("expected_amount") or 0,
                    "reduction": judgement.get("reduction"),
                }
            )

        if is_special:
            has_special_coverage = True

        evidence = {
            "article_no": r.get("article_no") or "특별약관",
            "page": r.get("page") or 1,
            "quote": r.get("raw_text") or "",
        }

        comparison_results.append(
            {
                "rider_name": r["name"],
                "policy_name": policy_name,
                "insurer": insurer,
                "verified": bool(r.get("verified")),
                "scenarios": scenarios,
                "evidence": evidence,
            }
        )

    slider = {
        "min": 1,
        "max": slider_max,
        "current": current_days,
        "target": target_days,
        "breakpoints": sorted(list(all_breakpoints)),
    }

    top_message = (
        "입원 기간에 따라 적용 가능한 특약 조건이 달라져요"
        if has_special_coverage
        else "선택하신 보험은 입원 기간에 따른 특약 조건이 없어요. 기본 입원일당 보장만 적용됩니다."
    )
    missed_amount_note = "현재 일수로는 적용되지 않는 특약이 있어요" if has_special_coverage else None

    return {
        "has_special_coverage": has_special_coverage,
        "top_message": top_message,
        "missed_amount_note": missed_amount_note,
        "slider": slider if has_special_coverage else None,
        "comparison": comparison_results,
        "disclaimer": (
            "⚠️위 계산은 약관 조항 기반 예시이며, 실제 지급 여부 및 금액은 보험사 심사 결과에 따라 달라질 수 있습니다."
        ),
        "notice": notice,
    }
