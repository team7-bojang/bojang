"""도메인 공통 상수 (judge 상태값·트리거 타입 등)."""

from enum import StrEnum


class JudgeStatus(StrEnum):
    ELIGIBLE = "eligible"
    CLAIMED = "claimed"
    BOUNDARY_NOT_MET = "boundary_not_met"
    WAITING_PERIOD_NOT_MET = "waiting_period_not_met"
    NOT_APPLICABLE = "not_applicable"
    POTENTIAL = "potential"  # verified=false 노출 등급


class TriggerType(StrEnum):
    입원 = "입원"
    수술 = "수술"
    진단 = "진단"
    통원 = "통원"
    내원 = "내원"
    골절 = "골절"
    치료 = "치료"
    사망 = "사망"
    후유장해 = "후유장해"
    기타 = "기타"
