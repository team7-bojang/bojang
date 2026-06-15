"""룰 엔진 — 판정은 룰, 설명은 LLM (설계서 6-3).

judge(case, rider) 는 DB·LLM 접근이 없는 **순수 함수**다.
탐색(F-02)·비교(F-03)는 반드시 이 함수만 호출한다 (판정 로직 중복 구현 금지).

판정 우선순위: waiting_period → boundary → eligible
분기: rider.claim_rule is None → 정액(boundaries.py) / not None → 실손(claim_rule.py)
"""

from app.judge.boundaries import judge_fixed
from app.judge.claim_rule import judge_reimbursement
from app.judge.types import Case, Judgement, Rider

__all__ = ["judge", "Case", "Rider", "Judgement"]


def judge(case: Case, rider: Rider) -> Judgement:
    if rider.get("claim_rule") is None:
        return judge_fixed(case, rider)
    return judge_reimbursement(case, rider)
