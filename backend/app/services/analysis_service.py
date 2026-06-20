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

    # 2. 내 가입 보험 목록 조회
    res_my = db.table("policies").select("*").eq("user_id", user_id).execute()
    my_policies = res_my.data or []

    notice = None
    is_dummy_used = False

    if not my_policies:
        my_policies = DUMMY_POLICIES
        is_dummy_used = True
        notice = (
            "실제 DB에 등록된 보험이 없어, 테스트를 위해 임의의 데모 보험 데이터"
            "(DB손해 3대질병, 메리츠 실손)를 임시로 추가하여 RAG 분석을 수행했습니다."
        )
        print("[analysis_service] 가입보험 없음 -> 임의 데모 보험 데이터 사용.")

    policy_ids = [p["id"] for p in my_policies]
    policy_names = {p["id"]: p["name"] for p in my_policies}

    # 3. RAG 유사 특약 검색
    query = f"{case_data.get('disease_name', '')} {case_data.get('disease_kcd', '')}"
    if case_data.get("surgery"):
        query += " 수술"
    if case_data.get("current_days"):
        query += f" {case_data['current_days']}일 입원"

    retriever = Retriever()
    chunks = []

    if not is_dummy_used:
        try:
            chunks = retriever.search(query, policy_ids=policy_ids, disease_kcd=case_data.get("disease_kcd"), k=15)
        except Exception as e:
            print(f"[analysis_service] RAG retriever.search failed: {e}")
            chunks = []

    if not chunks:
        chunks = DUMMY_CHUNKS
        if not notice:
            notice = (
                "RAG 검색 매칭 정보가 부족하여, 뇌경색 및 허리디스크 관련 "
                "임의의 데모 특약 데이터를 임시로 보완하여 분석을 실행했습니다."
            )
            print("[analysis_service] RAG 결과 없음 -> 임의 데모 특약 데이터 사용.")

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

        # 판정 엔진 입력에 맞게 캐스팅
        judge_case = {
            "disease_kcd": case_data.get("disease_kcd", ""),
            "surgery": bool(case_data.get("surgery", False)),
            "diag_days": int(case_data.get("diag_days") or 0),
            "current_days": int(case_data.get("current_days") or 0),
            "policy_elapsed_days": case_data.get("policy_elapsed_days"),
            "treatment_items": case_data.get("treatment_items") or [],
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
            "treatment_codes": get_rider_treatment_codes(db, rider_id, rider.get("name")),
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

        import os

        if os.environ.get("MOCK_LLM") == "True":
            explanation_data = {
                "explanation": (
                    f"약관 {rider.get('article_no', '조항')}에 근거하여 "
                    f"지급 상태가 [{status}]로 판정되었습니다."
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
                        f"약관 {rider.get('article_no', '조항')}에 근거하여 "
                        f"지급 상태가 [{status}]로 판정되었습니다."
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


def compare_scenarios(user_id: str, case_id: str, current_days: int, target_days: int) -> dict:
    """현재 입원 경과일수와 비교 대상 입원일수를 기준으로 보장 조건 차이를 비교합니다 (v2.1)."""
    db = get_client()

    # 1. 상황 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case_data = res_case.data[0]

    # 2. 내 가입 보험 목록 조회
    res_my = db.table("policies").select("*").eq("user_id", user_id).execute()
    my_policies = res_my.data or []

    notice = None
    is_dummy_used = False

    if not my_policies:
        my_policies = DUMMY_POLICIES
        is_dummy_used = True
        notice = (
            "실제 DB에 등록된 보험이 없어, 테스트를 위해 임의의 데모 보험 데이터"
            "(DB손해 3대질병)를 임시로 추가하여 퇴원 시점 비교표를 구성했습니다."
        )
        print("[analysis_service] 가입보험 없음 -> 임의 데모 보험 비교.")

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
        my_riders = DUMMY_RIDERS
        if not notice:
            notice = (
                "비교 가능한 입원 특약 데이터가 부족하여, 임의의 데모 입원 특약"
                "(DB손해 질병입원일당) 데이터를 임시로 보완하여 비교를 진행했습니다."
            )
            print("[analysis_service] 입원특약 없음 -> 임의 데모 입원특약 비교.")

    comparison_results = []
    all_breakpoints = set()
    has_special_coverage = False
    slider_max = 28

    for r in my_riders:
        trigger = r.get("trigger_type")
        if trigger != "입원":
            continue

        policy_id = r.get("policy_id")
        policy_name = policy_names.get(policy_id, "기타보험")
        insurer = policy_insurers.get(policy_id, "기타보험사")

        boundaries = r.get("boundaries") or []
        rider_breakpoints = []
        is_special = False

        for b in boundaries:
            cond_days = b.get("condition_days", 0)
            if cond_days > 1:
                all_breakpoints.add(cond_days)
                rider_breakpoints.append(cond_days)
                is_special = True
                if cond_days > slider_max:
                    slider_max = cond_days

        scenarios = []
        for days in [current_days, target_days]:
            temp_case = {
                "disease_kcd": case_data.get("disease_kcd", ""),
                "surgery": bool(case_data.get("surgery", False)),
                "diag_days": days,
                "current_days": days,
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

            calc_text = None
            amount_note = None
            gap_days = judgement.get("gap_days")

            if status == JudgeStatus.ELIGIBLE:
                unit_amount = r.get("unit_amount") or 10000
                if is_special:
                    if "정액" in (r.get("unit_basis") or ""):
                        calc_text = f"{unit_amount:,}원 (정액)"
                        amount_note = f"{unit_amount:,}원"
                    else:
                        calc_text = f"{unit_amount:,}원 × {days}일"
                        amount_note = f"{unit_amount * days:,}원"
                else:
                    calc_text = f"{unit_amount:,}원 × {days}일"
                    amount_note = f"{unit_amount * days:,}원"

            scenarios.append(
                {
                    "days": days,
                    "status": status,
                    "type": "special" if is_special else "base",
                    "label": "특약 조건" if is_special else "입원일당",
                    "calc": calc_text,
                    "amount_note": amount_note,
                    "gap_days": gap_days,
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
    missed_amount_note = (
        "현재 일수로는 적용되지 않는 특약이 있어요" if has_special_coverage else None
    )

    return {
        "has_special_coverage": has_special_coverage,
        "top_message": top_message,
        "missed_amount_note": missed_amount_note,
        "slider": slider if has_special_coverage else None,
        "comparison": comparison_results,
        "disclaimer": (
            "⚠️위 계산은 약관 조항 기반 예시이며, "
            "실제 지급 여부 및 금액은 보험사 심사 결과에 따라 달라질 수 있습니다."
        ),
        "notice": notice,
    }
