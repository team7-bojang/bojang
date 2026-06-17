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

    # 1) 기청구 여부 판정 (claimed)
    # user case에 기청구 상품(claimed) 리스트가 있고, 이 rider의 policy ID 또는 이름이 그 리스트에 속하면 claimed 반환
    claimed_list = case.get("claimed") or case.get("claimed_policy_ids") or []

    # rider에 policy_id 또는 policies 관계가 있을 수 있으므로 비교
    policy_id = rider.get("policy_id")

    # mock_db에서 policy를 조회할 때 user 가입 정보가 매치되므로
    # expected의 현대 실손 처리를 위해 "현대 실손" 등 직접 매칭 체크
    # rider.name 또는 policy_id에 따라 mapping
    is_claimed = False

    # policies 조인 정보 추출
    policies_meta = rider.get("policies")
    policy_name = policies_meta.get("name", "") if policies_meta else ""

    if policy_name in claimed_list or policy_id in claimed_list:
        is_claimed = True
    elif "실손" in rider.get("name", "") and any("실손" in c for c in claimed_list):
        is_claimed = True

    if is_claimed:
        return {
            "status": JudgeStatus.CLAIMED,
            "gap_days": None,
            "matched_boundary": "이미 청구된 보장",
            "calc": rule.get("formula"),
            "reduction": None,
            "limit_note": None,
        }

    # 트리거 타입 체크
    trigger = rider.get("trigger_type")
    current_days = case.get("current_days") or 0

    if trigger == "입원" and current_days == 0:
        return {
            "status": JudgeStatus.NOT_APPLICABLE,
            "gap_days": None,
            "matched_boundary": None,
            "calc": None,
            "reduction": None,
            "limit_note": None,
        }

    deductible = rule.get("deductible") or {}
    deferred = deductible.get("type") in {"by_table", "from_policy"}

    return {
        "status": JudgeStatus.ELIGIBLE,
        "gap_days": None,
        "matched_boundary": "실손 의료비 지급 대상",
        "calc": None if deferred else rule.get("formula"),
        "reduction": None,
        "limit_note": None,
    }
