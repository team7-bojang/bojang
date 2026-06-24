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
            "deductible": {"type": "max", "value": 30000, "rate": 0.3},
            "formula": "covered_amount - max(30000, covered_amount * 0.3)",
        }
    )
    result = judge(_case(), rider)
    assert result["calc"] == "covered_amount - max(30000, covered_amount * 0.3)"


def test_claim_rule_defers_calc_for_table_deductible():
    rider = _rider(claim_rule={"deductible": {"type": "by_table"}, "formula": "..."})
    result = judge(_case(), rider)
    assert result["calc"] is None


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
    rider = _rider(
        reductions=[{"until_elapsed_days": 365, "rate": 0.5, "note": "1년 미만 50% 감액"}]
    )
    # case에 coverage_amounts나 unit_amount를 매치시킬 수 있는게 아예 없어서 subscribed=None 인 상황
    case_data = _case(policy_elapsed_days=100) # 1년(365일) 미만 감액 구간에 들어옴
    result = judge(case_data, rider)
    
    assert result["status"] == "eligible"
    assert result["subscribed_amount"] is None
    assert result["expected_amount"] is None
    assert result["reduced_amount"] is None
