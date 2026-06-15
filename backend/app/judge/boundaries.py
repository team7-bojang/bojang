"""정액 보장 판정 — boundaries·deduct_days·limits·waiting·reduction (claim_rule=None).

⚠️ 스켈레톤: 골격·우선순위만 구현. 실제 판정 규칙은 이태경 소유 — 정답셋(tests/golden)
   기준으로 채운다. 현재는 계약(반환 구조)만 보장한다.
"""

from __future__ import annotations

from app.core.constants import JudgeStatus
from app.judge.types import Case, Judgement, Rider


def _empty(status: str) -> Judgement:
    return {
        "status": status,
        "gap_days": None,
        "matched_boundary": None,
        "calc": None,
        "reduction": None,
        "limit_note": None,
    }


def judge_fixed(case: Case, rider: Rider) -> Judgement:
    # 1) 면책기간(waiting_period) 미경과 판정
    waiting = rider.get("waiting_period_days")
    elapsed = case.get("policy_elapsed_days")
    if waiting and elapsed is not None and elapsed < waiting:
        out = _empty(JudgeStatus.WAITING_PERIOD_NOT_MET)
        out["gap_days"] = waiting - elapsed
        return out

    # 2) TODO: boundary(condition_days) vs current_days 비교 → boundary_not_met/eligible
    # 3) TODO: deduct_days·limits 반영 calc, reductions 반영 reduction/limit_note
    return _empty(JudgeStatus.NOT_APPLICABLE)
