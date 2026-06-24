"""정액 보장 판정 — boundaries·waiting·reduction (claim_rule=None).

판정 우선순위: waiting_period → boundary → eligible.
금액: 가입금액(coverage_amounts) × 일수(일당) 또는 일시금, 감액(reductions) 반영.
- 입원일당 → expected = 가입금액 × current_days
- 진단/일시금 → expected = 가입금액
- 미달(waiting/boundary) → expected=0, additional_amount=조건 충족 시 금액
- 감액 → reduced_amount = 감액 전 − 지급액  (CASE 2-2)
"""

from __future__ import annotations

from app.core.constants import JudgeStatus
from app.judge.amounts import resolve_subscribed
from app.judge.types import Case, Judgement, Rider, new_judgement


def _is_daily(rider: Rider, trigger: str | None) -> bool:
    """입원일당처럼 '일수 × 단가'로 지급되는지 여부."""
    unit_type = rider.get("unit_type") or ""
    return ("일" in unit_type or trigger == "입원") and "일시금" not in unit_type


def _fmt(amount: int | None) -> str:
    return f"{amount:,}원" if amount is not None else "가입금액 미입력"


def judge_fixed(case: Case, rider: Rider) -> Judgement:
    trigger = rider.get("trigger_type")
    current_days = case.get("current_days") or 0
    elapsed = case.get("policy_elapsed_days")

    subscribed = resolve_subscribed(case, rider)
    daily = _is_daily(rider, trigger)
    deduct = rider.get("deduct_days") or 0  # 공제일수 (입원일당만, 첫 N일 미지급)
    payable_days = max(0, current_days - deduct)
    base = None if subscribed is None else (subscribed * payable_days if daily else subscribed)

    # 1) 면책기간(waiting_period) 미경과
    waiting = rider.get("waiting_period_days")
    if waiting and elapsed is not None and elapsed < waiting:
        return new_judgement(
            JudgeStatus.WAITING_PERIOD_NOT_MET,
            gap_days=waiting - elapsed,
            subscribed_amount=subscribed,
            expected_amount=0,
            additional_amount=base,
            reason=f"가입 후 {waiting}일 경과 필요",
        )

    # 2) boundary(일수) 미달 — 입원일당 등
    boundaries = rider.get("boundaries") or []
    if trigger == "입원" and boundaries:
        thresholds = sorted(b.get("condition_days", 0) for b in boundaries)
        need = thresholds[0]
        if current_days < need:
            potential = (
                subscribed * max(0, need - deduct)
                if (daily and subscribed is not None)
                else base
            )
            return new_judgement(
                JudgeStatus.BOUNDARY_NOT_MET,
                gap_days=need - current_days,
                matched_boundary=f"{need}일 이상",
                subscribed_amount=subscribed,
                expected_amount=0,
                additional_amount=potential,
                reason=f"입원 {need}일 이상 필요",
            )

    # 3) eligible — 금액 산출 + 감액(reductions) 반영
    expected = base
    reduced = 0 if base is not None else None
    reduction = None
    reason = None
    limit_note = None

    if base is not None and elapsed is not None:
        for red in rider.get("reductions") or []:
            until = red.get("until_elapsed_days")
            rate = red.get("rate", 1.0)
            if until and elapsed < until:
                expected = int(base * rate)
                reduced = base - expected
                reduction = {
                    "applied": True,
                    "condition": f"가입 후 {until}일 미만",
                    "rate": rate,
                    "until_elapsed_days": until,
                }
                reason = "가입기간 미충족"  # CASE 2-2 감액 사유
                limit_note = red.get("note")
                break

    if base is None:
        calc = None
    elif daily:
        if deduct:
            calc = f"{_fmt(subscribed)} x ({current_days}일 - 공제 {deduct}일) = {_fmt(base)}"
        else:
            calc = f"{_fmt(subscribed)} x {current_days}일 = {_fmt(base)}"
        if reduced:
            calc = f"({calc}) x {int(reduction['rate'] * 100)}% 감액 = {_fmt(expected)}"
    else:
        calc = _fmt(subscribed)
        if reduced:
            calc = f"{calc} x {int(reduction['rate'] * 100)}% 감액 = {_fmt(expected)}"

    return new_judgement(
        JudgeStatus.ELIGIBLE,
        matched_boundary="지급 기준 충족",
        calc=calc,
        reduction=reduction,
        limit_note=limit_note,
        subscribed_amount=subscribed,
        expected_amount=expected,
        reduced_amount=reduced,
        additional_amount=0,
        reason=reason,
    )
