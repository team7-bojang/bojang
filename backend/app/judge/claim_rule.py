"""실손 등 정률·공제형 보장 판정 (claim_rule is not None).

설계서 6-4-1: status 는 trigger_type·claim_rule 매칭으로, calc 는 formula 기반 문자열.
expected_amount 는 formula 를 그대로 평가(covered_amount = 급여/비급여 버킷별 보상대상 의료비)해서 산출한다.
covered_amount 를 못 구하면(미입력) expected=None 으로 보류한다 (resolve_covered 참고).
⚠️ 이중차감 금지 — formula 를 신뢰하고 비율·공제를 추가로 곱·차감하지 않는다.
   deductible.type 이 by_table/from_policy 면 계산 보류(calc=None, expected=None).
"""

from __future__ import annotations

from app.core.constants import JudgeStatus
from app.judge.amounts import eval_formula, resolve_covered, resolve_subscribed
from app.judge.types import Case, Judgement, Rider, new_judgement


def _covered_label(rider: Rider) -> str:
    """covered_amount 가 어느 버킷에서 왔는지 사람이 읽을 라벨."""
    medical_category = (rider.get("claim_rule") or {}).get("medical_category") or ""
    if "비급여" in medical_category:
        return "비급여 의료비"
    if "급여" in medical_category:
        return "급여 본인부담"
    return "보상대상 의료비"


def _reimbursement_calc(formula: str | None, covered: int | None, expected: int | None, label: str) -> str | None:
    """실손 calc 문자열 — formula 의 `covered_amount` 토큰을 '버킷라벨 값원'으로 치환해
    급여 본인부담/비급여 중 어느 값이 들어갔는지 드러낸다. 예: '급여 본인부담 50,000원 × 0.8 = 40,000원'.
    값(covered)이나 결과(expected)가 없으면 None(보류)."""
    if not formula or covered is None or expected is None:
        return None
    readable = formula.replace("covered_amount", f"{label} {covered:,}원").replace("*", "×")
    return f"{readable} = {expected:,}원"


def judge_reimbursement(case: Case, rider: Rider) -> Judgement:
    rule = rider.get("claim_rule") or {}
    subscribed = resolve_subscribed(case, rider)

    # 1) 기청구 여부 — 이미 청구한 보험이면 claimed
    claimed_list = case.get("claimed") or []
    policy_name = ""
    policies_meta = rider.get("policies")
    if isinstance(policies_meta, dict):
        policy_name = policies_meta.get("name", "")
    name = rider.get("name", "")
    is_claimed = (
        policy_name in claimed_list
        or rider.get("policy_id") in claimed_list
        or ("실손" in name and any("실손" in str(c) for c in claimed_list))
    )
    if is_claimed:
        return new_judgement(
            JudgeStatus.CLAIMED,
            matched_boundary="이미 청구된 보장",
            calc=rule.get("formula"),
            subscribed_amount=subscribed,
            reason="이미 청구함",
        )

    # 2) 트리거 불일치
    trigger = rider.get("trigger_type")
    if trigger == "입원" and (case.get("current_days") or 0) == 0:
        return new_judgement(JudgeStatus.NOT_APPLICABLE, reason="입원 상태 아님")

    # 3) 지급 대상 — formula 평가 (보류 조건 분기)
    deductible = rule.get("deductible") or {}
    deferred = deductible.get("type") in {"by_table", "from_policy"}
    formula = rule.get("formula")
    # covered_amount 는 medical_category(급여/비급여) 버킷별 보상대상 의료비. 못 구하면 None → 보류.
    covered = None if deferred else resolve_covered(case, rider)
    expected = eval_formula(formula, covered)
    # calc 는 어느 버킷(급여 본인부담/비급여)이 얼마 들어갔는지 드러내는 문자열로 만든다.
    calc = None if deferred else _reimbursement_calc(formula, covered, expected, _covered_label(rider))

    return new_judgement(
        JudgeStatus.ELIGIBLE,
        matched_boundary="실손 의료비 지급 대상",
        calc=calc,
        subscribed_amount=subscribed,
        expected_amount=expected,
        reduced_amount=0,
        additional_amount=0,
        limit_note="표 공제 적용 — 정밀 금액 보험사 심사" if deferred else None,
    )
