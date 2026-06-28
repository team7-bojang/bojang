"""룰 엔진 계약 테스트 (순수 함수 — DB/LLM 불필요).

판정 로직은 이태경이 정답셋 기준으로 채운다. 여기서는 반환 구조(계약)와
claim_rule 분기·waiting_period 우선순위만 고정한다.
"""

from app.judge import Rider, judge
from app.judge.types import Case

_JUDGEMENT_KEYS = {
    "status",
    "gap_days",
    "matched_boundary",
    "calc",
    "reduction",
    "limit_note",
    "subscribed_amount",
    "expected_amount",
    "reduced_amount",
    "additional_amount",
    "reason",
}


def _case(**over) -> Case:
    base: Case = {
        "disease_kcd": "I63",
        "surgery": False,
        "diag_days": 7,
        "current_days": 3,
        "policy_elapsed_days": 800,
    }
    base.update(over)
    return base


def _rider(**over) -> Rider:
    base: Rider = {
        "trigger_type": "입원",
        "boundaries": [],
        "exclusions": [],
        "limits": [],
        "waiting_period_days": None,
        "reductions": [],
        "deduct_days": 0,
        "unit_amount": None,
        "unit_type": None,
        "claim_rule": None,
        "source_pages": [],
    }
    base.update(over)
    return base


def test_judgement_contract_shape():
    result = judge(_case(), _rider())
    assert set(result.keys()) == _JUDGEMENT_KEYS


def test_waiting_period_not_met_has_priority():
    # 면책 90일, 가입 후 30일 경과 → 미경과
    result = judge(_case(policy_elapsed_days=30), _rider(waiting_period_days=90, unit_amount=10000))
    assert result["status"] == "waiting_period_not_met"
    assert result["gap_days"] == 60


def test_claim_rule_branch_uses_formula_for_simple_deductible():
    rider = _rider(
        claim_rule={
            "medical_category": "비급여",
            "deductible": {"type": "max", "value": 30000, "rate": 0.3},
            "formula": "covered_amount - max(30000, covered_amount * 0.3)",
        }
    )
    result = judge(_case(non_covered_amount=100000), rider)
    # 100,000 - max(30000, 30000) = 70,000
    assert result["expected_amount"] == 70000
    # calc 는 covered_amount 가 아니라 버킷 라벨+값으로 표시된다.
    assert "covered_amount" not in result["calc"]
    assert "비급여 의료비 100,000원" in result["calc"]
    assert result["calc"].endswith("= 70,000원")


def test_reimbursement_calc_labels_patient_paid_bucket():
    rider = _rider(claim_rule={"medical_category": "급여", "formula": "covered_amount * 0.8"})
    result = judge(_case(patient_paid_amount=50000), rider)
    assert result["expected_amount"] == 40000
    assert result["calc"] == "급여 본인부담 50,000원 × 0.8 = 40,000원"


def test_claim_rule_defers_calc_for_table_deductible():
    rider = _rider(claim_rule={"deductible": {"type": "by_table"}, "formula": "..."})
    result = judge(_case(), rider)
    assert result["calc"] is None


def test_reimbursement_covered_uses_patient_paid_for_benefit_category():
    # 급여 실손: covered_amount = patient_paid_amount (급여 본인부담). payment_amount(합계)는 쓰지 않는다.
    rider = _rider(claim_rule={"medical_category": "급여", "formula": "covered_amount * 0.8"})
    case = _case(patient_paid_amount=700000, non_covered_amount=500000, payment_amount=1200000)
    result = judge(case, rider)
    assert result["status"] == "eligible"
    assert result["expected_amount"] == 560000  # 700000 * 0.8 (1200000 합계가 아님)


def test_reimbursement_covered_uses_non_covered_for_non_benefit_category():
    # 비급여 실손: covered_amount = non_covered_amount (비급여 의료비)
    rider = _rider(claim_rule={"medical_category": "비급여", "formula": "covered_amount * 0.7"})
    case = _case(patient_paid_amount=700000, non_covered_amount=500000, payment_amount=1200000)
    result = judge(case, rider)
    assert result["expected_amount"] == 350000  # 500000 * 0.7


def test_reimbursement_covered_routes_three_major_non_benefit_to_non_covered():
    # "3대비급여"도 "비급여" 부분문자열 → 비급여 버킷으로 라우팅
    rider = _rider(claim_rule={"medical_category": "3대비급여", "formula": "covered_amount * 0.7"})
    result = judge(_case(non_covered_amount=500000), rider)
    assert result["expected_amount"] == 350000


def test_reimbursement_defers_when_no_bucket_amount():
    # 급여/비급여 입력이 없으면 payment_amount(합계)로 폴백하지 않고 보류(expected=None)
    rider = _rider(claim_rule={"medical_category": "급여", "formula": "covered_amount * 0.8"})
    result = judge(_case(payment_amount=1200000), rider)
    assert result["status"] == "eligible"
    assert result["expected_amount"] is None


def test_resolve_subscribed_type_mismatch_p2_1():
    # P2-1: rider id가 정수 42이고 coverage_amounts 딕셔너리 키가 문자열 "42"인 경우
    case_dict = _case(coverage_amounts={"42": {"amount": 50000}})
    rider = _rider(id=42)
    result = judge(case_dict, rider)
    assert result["subscribed_amount"] == 50000

    # 리스트 포맷의 매칭 확인
    case_list = _case(coverage_amounts=[{"rider_id": "42", "amount": 50000}])
    result = judge(case_list, rider)
    assert result["subscribed_amount"] == 50000


def test_judge_fixed_subscribed_is_none_with_reduction_p2_2():
    # P2-2: subscribed가 None이고 감액(reductions) 조건에 해당하는 경우 500 TypeError 없이 정상 평가 확인
    rider = _rider(reductions=[{"until_elapsed_days": 365, "rate": 0.5, "note": "1년 미만 50% 감액"}])
    # case에 coverage_amounts나 unit_amount를 매치시킬 수 있는게 아예 없어서 subscribed=None 인 상황
    case_data = _case(policy_elapsed_days=100)  # 1년(365일) 미만 감액 구간에 들어옴
    result = judge(case_data, rider)

    assert result["status"] == "eligible"
    assert result["subscribed_amount"] is None
    assert result["expected_amount"] is None
    assert result["reduced_amount"] is None


def test_judge_fixed_reduction_schema_compatibility():
    # 감액 적용 시 reduction 스키마가 이전 코드 규격(applied, until_elapsed_days)을 만족하는지 확인
    # 가입금액은 coverage_amounts(개인 입력)에서만 받는다 (unit_amount 폴백 없음).
    rider = _rider(id="r1", reductions=[{"until_elapsed_days": 365, "rate": 0.5, "note": "1년 미만 50% 감액"}])
    case_data = _case(policy_elapsed_days=100, coverage_amounts=[{"rider_id": "r1", "amount": 100000}])
    result = judge(case_data, rider)

    assert result["status"] == "eligible"
    assert result["expected_amount"] == 150000
    assert result["reduced_amount"] == 150000
    assert result["reduction"] is not None
    assert result["reduction"]["applied"] is True
    assert result["reduction"]["until_elapsed_days"] == 365
    assert result["reduction"]["rate"] == 0.5


def test_judge_fixed_no_unit_amount_fallback_defers():
    # 가입금액 미입력이면 unit_amount(시드 기본값 등 임의값)로 폴백하지 않고 보류한다.
    rider = _rider(unit_amount=10000)  # unit_amount 가 있어도 가입금액 입력이 없으면 쓰지 않는다
    result = judge(_case(), rider)
    assert result["status"] == "eligible"
    assert result["subscribed_amount"] is None
    assert result["expected_amount"] is None
    assert result["calc"] is None
