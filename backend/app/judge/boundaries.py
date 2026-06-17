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

    # 트리거 타입 체크 및 매칭
    trigger = rider.get("trigger_type")
    
    # 상황 데이터 추출
    current_days = case.get("current_days") or 0
    surgery = case.get("surgery") or False
    disease_kcd = case.get("disease_kcd") or ""
    disease_name = case.get("disease") or "" # case_service/eval_golden 호환

    if trigger == "입원" and current_days == 0:
        return _empty(JudgeStatus.NOT_APPLICABLE)
    if trigger == "수술" and not surgery:
        return _empty(JudgeStatus.NOT_APPLICABLE)

    # 뇌혈관 입원일당 등 특정 질병 제한 특약 처리
    rider_name = rider.get("name", "")
    if "뇌혈관" in rider_name or "뇌졸중" in rider_name:
        if not (disease_kcd.startswith("I6") or "뇌경색" in disease_name or "뇌졸중" in disease_name):
            return _empty(JudgeStatus.NOT_APPLICABLE)
            
    if "암" in rider_name:
        if not (disease_kcd.startswith("C") or "암" in disease_name):
            return _empty(JudgeStatus.NOT_APPLICABLE)

    # 2) boundary(condition_days) vs current_days 비교
    boundaries = rider.get("boundaries") or []
    
    if trigger == "입원" and boundaries:
        # 입원일 경계 만족 여부 체크
        sorted_bounds = sorted(boundaries, key=lambda x: x.get("condition_days", 0))
        matched_b = None
        
        for b in sorted_bounds:
            cond_days = b.get("condition_days", 0)
            if current_days >= cond_days:
                matched_b = b
            else:
                # 경계 미달 (gap_days 계산)
                gap = cond_days - current_days
                out = _empty(JudgeStatus.BOUNDARY_NOT_MET)
                out["gap_days"] = gap
                out["matched_boundary"] = f"{cond_days}일 이상"
                return out
                
        if not matched_b:
            first_cond = sorted_bounds[0].get("condition_days", 0)
            out = _empty(JudgeStatus.BOUNDARY_NOT_MET)
            out["gap_days"] = first_cond - current_days
            return out

    # 3) calc 및 reductions 반영
    unit_amount = rider.get("unit_amount") or 30000
    calc = f"{unit_amount:,}원 x {current_days}일 = {unit_amount * current_days:,}원"
    
    reduction = None
    limit_note = None
    reductions = rider.get("reductions") or []
    
    if reductions and elapsed is not None:
        for red in reductions:
            until_days = red.get("until_elapsed_days")
            if until_days and elapsed < until_days:
                rate = red.get("rate", 1.0)
                reduction = {
                    "condition": f"계약일로부터 {until_days}일 미만",
                    "rate": rate
                }
                calc = f"({calc}) x {int(rate*100)}% 감액 = {int(unit_amount * current_days * rate):,}원"
                limit_note = red.get("note")
                break

    return {
        "status": JudgeStatus.ELIGIBLE,
        "gap_days": None,
        "matched_boundary": "지급 기준 충족",
        "calc": calc,
        "reduction": reduction,
        "limit_note": limit_note
    }

