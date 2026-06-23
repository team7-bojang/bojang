"""실손 등 정률·공제형 보장 판정 (claim_rule is not None).

설계서 6-4-1: status 는 trigger_type·claim_rule 매칭으로, calc 는 formula 기반 문자열.
expected_amount 는 formula 를 그대로 평가(covered_amount = 결제금액)해서 산출한다.
⚠️ 이중차감 금지 — formula 를 신뢰하고 비율·공제를 추가로 곱·차감하지 않는다.
   deductible.type 이 by_table/from_policy 면 계산 보류(calc=None, expected=None).
"""

from __future__ import annotations

from app.core.constants import JudgeStatus
from app.judge.amounts import eval_formula, resolve_covered, resolve_subscribed
from app.judge.types import Case, Judgement, Rider, new_judgement


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
    # covered_amount 는 특약별 보상대상 의료비 (급여/비급여 분리). 없으면 총 결제금액 폴백.
    expected = None if deferred else eval_formula(formula, resolve_covered(case, rider))

    return new_judgement(
        JudgeStatus.ELIGIBLE,
        matched_boundary="실손 의료비 지급 대상",
        calc=None if deferred else formula,
        subscribed_amount=subscribed,
        expected_amount=expected,
        reduced_amount=0,
        additional_amount=0,
        limit_note="표 공제 적용 — 정밀 금액 보험사 심사" if deferred else None,
    )
