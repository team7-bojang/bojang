"""룰 엔진 계약 테스트 (순수 함수 — DB/LLM 불필요).

판정 로직은 이태경이 정답셋 기준으로 채운다. 여기서는 반환 구조(계약)와
claim_rule 분기·waiting_period 우선순위만 고정한다.
"""

from app.judge import Rider, judge
from app.judge.amounts import eval_formula, resolve_covered, resolve_subscribed
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


# ─────────────────────────────────────────────────────────────
# not_applicable(해당 없음) 필터 — 오탐 방지 (judge/__init__.py)
# 트리거 불일치 / 사망 / 룰테이블(질병군·치료항목) / 키워드 폴백 분기를 고정한다.
# ─────────────────────────────────────────────────────────────


def test_na_inpatient_rider_but_not_admitted():
    # 입원 특약인데 입원 일수(current_days)가 0 → 해당 없음(완전 무관, 숨김)
    result = judge(_case(current_days=0), _rider(trigger_type="입원"))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "입원 상태 아님"


def test_na_surgery_rider_but_no_surgery():
    # 수술 특약인데 수술 안 함
    result = judge(_case(surgery=False), _rider(trigger_type="수술"))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "수술 아님"


def test_na_death_rider_when_not_deceased():
    # 사망 특약인데 생존 → 해당 없음
    result = judge(_case(), _rider(name="사망보험금", trigger_type="사망"))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "사망 보장 — 해당 없음"


def test_na_required_treatment_not_met():
    # 룰테이블: 요구 치료항목(MRI)인데 케이스엔 XRAY만 → 해당 없음
    result = judge(_case(treatment_codes=["XRAY"]), _rider(require_treatments=["MRI"]))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "요구 치료항목 미충족"


def test_na_excluded_disease_group_is_conditional():
    # 룰테이블: 제외 질병군(유사암)에 걸림 → 해당 없음 + 진단 확정 시 받을 금액(additional)
    rider = _rider(id="r1", exclude_groups=["유사암"])
    case = _case(disease_groups=["유사암"], coverage_amounts={"r1": 5_000_000})
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "제외 질병군 (유사암 등)"
    assert result["additional_amount"] == 5_000_000


def test_na_required_disease_group_not_met_is_conditional():
    # 룰테이블: 요구 질병군(뇌혈관) 미충족 → 해당 없음(conditional)
    rider = _rider(id="r1", require_groups=["뇌혈관"])
    case = _case(disease_groups=["기타"], coverage_amounts={"r1": 3_000_000})
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "요구 질병군 미충족"
    assert result["additional_amount"] == 3_000_000


def test_na_keyword_fallback_injury_rider_for_disease_case():
    # 룰테이블 없음 → 키워드 폴백: 상해 특약인데 상해 상황 아님(I63 질병 KCD)
    result = judge(_case(), _rider(name="상해입원"))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "상해 상황 아님"


def test_na_keyword_fallback_cancer_rider_for_non_cancer_is_conditional():
    # 키워드 폴백: 암진단비인데 비암(허리디스크) → 해당 없음 + 진단 확정 시 받을 금액
    rider = _rider(id="r1", name="암진단비", trigger_type="진단")
    case = _case(
        disease_kcd="M51",
        disease_name="허리디스크",
        coverage_amounts=[{"rider_id": "r1", "amount": 30_000_000}],
    )
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "암 진단 확정 필요"
    assert result["additional_amount"] == 30_000_000


# ─────────────────────────────────────────────────────────────
# 금액 산출 보조 (judge/amounts.py) — 순수 함수 직접 검증.
# ─────────────────────────────────────────────────────────────


def test_resolve_subscribed_single_number_applies_to_all():
    # 단일 숫자 가입금액(Case2 비교 시나리오) → 모든 특약에 동일 적용
    assert resolve_subscribed(_case(coverage_amounts=50000), _rider()) == 50000


def test_resolve_subscribed_matches_by_rider_name():
    # id 없이 특약명으로 매칭
    case = _case(coverage_amounts={"입원일당": 30000})
    assert resolve_subscribed(case, _rider(name="입원일당")) == 30000


def test_resolve_covered_prefers_per_rider_over_bucket():
    # per-rider covered_amounts 가 급여/비급여 버킷보다 우선 (버킷 non_covered 무시)
    case = _case(covered_amounts=[{"rider_id": "r1", "amount": 80000}], non_covered_amount=999999)
    rider = _rider(id="r1", claim_rule={"medical_category": "비급여"})
    assert resolve_covered(case, rider) == 80000


def test_eval_formula_handles_unary_minus():
    # 단항 음수 평가
    assert eval_formula("covered_amount - -1000", 5000) == 6000


def test_eval_formula_defers_on_unsupported_operator():
    # 미지원 연산자(거듭제곱) → 보류(None)
    assert eval_formula("covered_amount ** 2", 1000) is None


def test_eval_formula_defers_on_unknown_variable():
    # 미지 변수(상급병실료 등) → 보류(None)
    assert eval_formula("상급병실료 - 50000", 1000) is None


# ── 키워드 폴백 나머지 분기 (질병/뇌혈관/심장/척추) ──


def test_na_keyword_fallback_disease_rider_for_injury_case():
    # 질병 특약인데 상해(골절) 상황 → 해당 없음
    result = judge(_case(disease_kcd="S72", disease_name="대퇴골 골절"), _rider(name="질병입원"))
    assert result["status"] == "not_applicable"
    assert result["reason"] == "질병 상황 아님"


def test_na_keyword_fallback_brain_rider_for_non_brain_is_conditional():
    # 뇌혈관 진단비인데 비뇌질환 → 해당 없음 + 진단 확정 시 받을 금액
    rider = _rider(id="r1", name="뇌혈관질환진단비", trigger_type="진단")
    case = _case(disease_kcd="M51", disease_name="허리디스크", coverage_amounts={"r1": 20_000_000})
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "뇌혈관 질환 진단 확정 필요"
    assert result["additional_amount"] == 20_000_000


def test_na_keyword_fallback_heart_rider_for_non_heart_is_conditional():
    # 심장 진단비인데 비심장질환 → 해당 없음(conditional)
    rider = _rider(id="r1", name="허혈성심장질환진단비", trigger_type="진단")
    case = _case(disease_kcd="M51", disease_name="허리디스크", coverage_amounts={"r1": 10_000_000})
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "심장 질환 진단 확정 필요"
    assert result["additional_amount"] == 10_000_000


def test_na_keyword_fallback_spine_rider_for_non_spine_is_conditional():
    # 척추 진단비인데 비척추질환 → 해당 없음(conditional)
    rider = _rider(id="r1", name="척추질환진단비", trigger_type="진단")
    case = _case(disease_kcd="I10", disease_name="고혈압", coverage_amounts={"r1": 8_000_000})
    result = judge(case, rider)
    assert result["status"] == "not_applicable"
    assert result["reason"] == "척추 질환 진단 확정 필요"
    assert result["additional_amount"] == 8_000_000


# ── amounts dict/list 나머지 경로 ──


def test_resolve_covered_dict_format_by_rider_id():
    # 실손 covered_amounts 가 dict 포맷일 때 rider id 로 매칭
    case = _case(covered_amounts={"r1": 80000})
    rider = _rider(id="r1", claim_rule={"medical_category": "비급여"})
    assert resolve_covered(case, rider) == 80000


def test_resolve_subscribed_list_by_coverage_key():
    # list 포맷에서 coverage_key(특약명)로 매칭 (id 없음)
    case = _case(coverage_amounts=[{"coverage_key": "입원일당", "amount": 25000}])
    assert resolve_subscribed(case, _rider(name="입원일당")) == 25000
