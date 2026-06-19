"""룰 엔진 — 판정은 룰, 설명은 LLM (설계서 6-3).

judge(case, rider) 는 DB·LLM 접근이 없는 **순수 함수**다.
탐색(F-02)·비교(F-03)는 반드시 이 함수만 호출한다 (판정 로직 중복 구현 금지).

판정 우선순위: waiting_period → boundary → eligible
분기: rider.claim_rule is None → 정액(boundaries.py) / not None → 실손(claim_rule.py)
"""

from app.core.constants import JudgeStatus
from app.judge.boundaries import judge_fixed
from app.judge.claim_rule import judge_reimbursement
from app.judge.types import Case, Judgement, Rider

__all__ = ["judge", "Case", "Rider", "Judgement"]


def _empty_not_applicable() -> Judgement:
    return {
        "status": JudgeStatus.NOT_APPLICABLE,
        "gap_days": None,
        "matched_boundary": None,
        "calc": None,
        "reduction": None,
        "limit_note": None,
    }


def judge(case: Case, rider: Rider) -> Judgement:
    # 1. 공통 상황 적합성(Applicability) 판정
    rider_name = rider.get("name") or ""
    trigger = rider.get("trigger_type") or ""

    disease_kcd = case.get("disease_kcd") or ""
    disease_name = case.get("disease_name") or case.get("disease") or ""
    surgery = case.get("surgery") or False
    current_days = case.get("current_days") or 0

    # 1-1) 트리거 조건 불일치
    if trigger == "입원" and current_days == 0:
        return _empty_not_applicable()
    if trigger == "수술" and not surgery:
        return _empty_not_applicable()

    # 1-2) 사망 특약 필터링
    if "사망" in rider_name or trigger == "사망":
        if not case.get("is_deceased") and not case.get("death"):
            return _empty_not_applicable()

    # 1-3) 질병/상해 카테고리 필터링
    is_injury_kcd = disease_kcd.startswith("S") or disease_kcd.startswith("T")
    is_injury_name = any(w in disease_name for w in ["상해", "골절", "재해", "사고", "다침"])
    is_injury_case = is_injury_kcd or is_injury_name

    # 상해 특약인데 질병 상황인 경우 제외
    if any(w in rider_name for w in ["상해", "재해", "골절"]):
        if not is_injury_case:
            return _empty_not_applicable()

    # 질병 특약인데 상해 상황인 경우 제외
    if any(w in rider_name for w in ["질병", "암", "뇌", "심장"]):
        if is_injury_case and not any(w in disease_name for w in ["질병", "암", "뇌", "심장"]):
            return _empty_not_applicable()

    # 1-4) 특정 질병군 적합성 상세 필터링
    # 뇌혈관/뇌졸중/뇌출혈 그룹
    if any(w in rider_name for w in ["뇌혈관", "뇌졸중", "뇌출혈", "뇌경색"]):
        is_brain_disease = (
            disease_kcd.startswith("I6") or
            any(w in disease_name for w in ["뇌경색", "뇌졸중", "뇌출혈", "뇌혈관"])
        )
        if not is_brain_disease:
            return _empty_not_applicable()

    # 암/악성신생물/유사암 그룹
    if any(w in rider_name for w in ["암", "악성신생물", "유사암", "제자리암"]):
        is_cancer_disease = (
            disease_kcd.startswith("C") or
            disease_kcd.startswith("D0") or
            disease_kcd.startswith("D3") or
            disease_kcd.startswith("D4") or
            any(w in disease_name for w in ["암", "악성신생물", "종양", "유사암", "경계성"])
        )
        if not is_cancer_disease:
            return _empty_not_applicable()

    # 심장/심근경색/허혈성심장질환 그룹
    if any(w in rider_name for w in ["심근경색", "허혈성", "심장", "심혈관"]):
        is_heart_disease = (
            disease_kcd.startswith("I2") or
            any(w in disease_name for w in ["심근경색", "허혈성", "심장", "심혈관"])
        )
        if not is_heart_disease:
            return _empty_not_applicable()

    # 추간판/디스크/척추 그룹
    if any(w in rider_name for w in ["추간판", "디스크", "척추", "탈출증"]):
        is_spine_disease = (
            disease_kcd.startswith("M50") or
            disease_kcd.startswith("M51") or
            disease_kcd.startswith("M52") or
            disease_kcd.startswith("M53") or
            disease_kcd.startswith("M54") or
            any(w in disease_name for w in ["디스크", "추간판", "척추", "탈출증"])
        )
        if not is_spine_disease:
            return _empty_not_applicable()

    # 2. 세부 정액/실손 판정 위임
    if rider.get("claim_rule") is None:
        return judge_fixed(case, rider)
    return judge_reimbursement(case, rider)

