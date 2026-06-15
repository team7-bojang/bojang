"""실손 등 정률·공제형 보장 판정 (claim_rule is not None).

설계서 6-4-1: status 는 trigger_type·claim_rule(cause_type/visit_type) 매칭으로 판정,
calc 는 claim_rule.formula 기반 "계산 구조" 문자열.
⚠️ 이중차감 금지 — formula 를 그대로 신뢰하고 비율·공제를 추가로 곱·차감하지 않는다.

⚠️ 스켈레톤: 계약(반환 구조)만 보장. 실제 매칭 규칙은 이태경 소유.
"""

from __future__ import annotations

from app.core.constants import JudgeStatus
from app.judge.types import Case, Judgement, Rider


def judge_reimbursement(case: Case, rider: Rider) -> Judgement:
    rule = rider.get("claim_rule") or {}

    # TODO: case 와 claim_rule(cause_type/visit_type) 매칭으로 status 판정
    # TODO: deductible 유형별 calc 산출
    #   - null/max/fixed → formula 로 계산식 문자열
    #   - by_table/from_policy → calc=None, "공제 기준 검수 후 계산" 보류
    deductible = rule.get("deductible") or {}
    deferred = deductible.get("type") in {"by_table", "from_policy"}

    return {
        "status": JudgeStatus.NOT_APPLICABLE,
        "gap_days": None,
        "matched_boundary": None,
        "calc": None if deferred else rule.get("formula"),
        "reduction": None,
        "limit_note": None,
    }
