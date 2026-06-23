"""룰 엔진 — 판정은 룰, 설명은 LLM (설계서 6-3).

judge(case, rider) 는 DB·LLM 접근이 없는 **순수 함수**다.
탐색(F-02·CASE1)·비교(F-03·CASE2)는 반드시 이 함수만 호출한다 (판정 로직 중복 구현 금지).

판정 우선순위: waiting_period → boundary → eligible
분기: rider.claim_rule is None → 정액(boundaries.py) / not None → 실손(claim_rule.py)

not_applicable 도 사유(reason)를 함께 반환한다:
- 트리거 자체가 무관(입원 안 함 등) → additional 없음 → 화면에서 숨김
- 진단명 등 조건만 미충족 → additional_amount(진단 시 받을 금액) → CASE 2-1 "추가 보장 가능성"
"""

from app.core.constants import JudgeStatus
from app.judge.amounts import resolve_subscribed
from app.judge.boundaries import judge_fixed
from app.judge.claim_rule import judge_reimbursement
from app.judge.types import Case, Judgement, Rider, new_judgement

__all__ = ["judge", "Case", "Rider", "Judgement"]


def judge(case: Case, rider: Rider) -> Judgement:
    rider_name = rider.get("name") or ""
    trigger = rider.get("trigger_type") or ""

    disease_kcd = case.get("disease_kcd") or ""
    disease_name = case.get("disease_name") or ""
    surgery = case.get("surgery") or False
    current_days = case.get("current_days") or 0

    subscribed = resolve_subscribed(case, rider)

    def na(reason: str, conditional: bool = False) -> Judgement:
        """해당 없음. conditional=True 면 진단 충족 시 받을 금액(additional)을 함께 준다."""
        return new_judgement(
            JudgeStatus.NOT_APPLICABLE,
            reason=reason,
            subscribed_amount=subscribed if conditional else None,
            additional_amount=subscribed if conditional else None,
        )

    # 1-1) 트리거 조건 불일치 (완전 무관 → 숨김)
    if trigger == "입원" and current_days == 0:
        return na("입원 상태 아님")
    if trigger == "수술" and not surgery:
        return na("수술 아님")

    # 1-2) 사망 특약 필터링
    if "사망" in rider_name or trigger == "사망":
        if not case.get("is_deceased"):
            return na("사망 보장 — 해당 없음")

    # 1-3) 룰테이블 기반 정밀 매칭 (resolver가 채워준 경우 — 키워드 휴리스틱보다 우선)
    require_groups = set(rider.get("require_groups") or [])
    exclude_groups = set(rider.get("exclude_groups") or [])
    require_treatments = set(rider.get("require_treatments") or [])
    case_groups = set(case.get("disease_groups") or [])
    case_treatments = set(case.get("treatment_codes") or [])

    # 치료항목 요구 미충족 → 해당 없음 (예: MRI/CT검사비인데 XRAY만 한 경우)
    if require_treatments and not (require_treatments & case_treatments):
        return na("요구 치료항목 미충족")

    if require_groups or exclude_groups:
        # 룰테이블 데이터가 있으면 집합 매칭으로 판정한다 (아래 키워드 폴백 생략).
        if exclude_groups and (case_groups & exclude_groups):
            return na("제외 질병군 (유사암 등)", conditional=True)
        if require_groups and not (case_groups & require_groups):
            return na("요구 질병군 미충족", conditional=True)
    else:
        # 1-4) (폴백) 키워드+KCD 휴리스틱. ⚠️ 임시 — resolver(룰테이블)로 완전 대체 예정.
        is_injury_kcd = disease_kcd.startswith("S") or disease_kcd.startswith("T")
        is_injury_name = any(w in disease_name for w in ["상해", "골절", "재해", "사고", "다침"])
        is_injury_case = is_injury_kcd or is_injury_name

        if any(w in rider_name for w in ["상해", "재해", "골절"]):
            if not is_injury_case:
                return na("상해 상황 아님")

        if any(w in rider_name for w in ["질병", "암", "뇌", "심장"]):
            if is_injury_case and not any(w in disease_name for w in ["질병", "암", "뇌", "심장"]):
                return na("질병 상황 아님")

        if any(w in rider_name for w in ["뇌혈관", "뇌졸중", "뇌출혈", "뇌경색"]):
            is_brain = disease_kcd.startswith("I6") or any(
                w in disease_name for w in ["뇌경색", "뇌졸중", "뇌출혈", "뇌혈관"]
            )
            if not is_brain:
                return na("뇌혈관 질환 진단 확정 필요", conditional=True)

        if any(w in rider_name for w in ["암", "악성신생물", "유사암", "제자리암"]):
            is_cancer = disease_kcd.startswith(("C", "D0", "D3", "D4")) or any(
                w in disease_name for w in ["암", "악성신생물", "종양", "유사암", "경계성"]
            )
            if not is_cancer:
                return na("암 진단 확정 필요", conditional=True)

        if any(w in rider_name for w in ["심근경색", "허혈성", "심장", "심혈관"]):
            is_heart = disease_kcd.startswith("I2") or any(
                w in disease_name for w in ["심근경색", "허혈성", "심장", "심혈관"]
            )
            if not is_heart:
                return na("심장 질환 진단 확정 필요", conditional=True)

        if any(w in rider_name for w in ["추간판", "디스크", "척추", "탈출증"]):
            is_spine = disease_kcd.startswith(("M50", "M51", "M52", "M53", "M54")) or any(
                w in disease_name for w in ["디스크", "추간판", "척추", "탈출증"]
            )
            if not is_spine:
                return na("척추 질환 진단 확정 필요", conditional=True)

    # 2) 정액/실손 세부 판정 위임
    if rider.get("claim_rule") is None:
        return judge_fixed(case, rider)
    return judge_reimbursement(case, rider)
