"""상황 입력(case) 요청/응답 스키마 (SCR-03)."""

from pydantic import BaseModel


class CaseCreate(BaseModel):
    disease_kcd: str
    disease_name: str
    surgery: bool = False
    diag_days: int | None = None
    current_days: int | None = None
    claimed_policy_ids: list[str] = []
    policy_elapsed_days: int | None = None  # None → 면책·감액 "확인 불가"


class CaseCreated(BaseModel):
    case_id: str
