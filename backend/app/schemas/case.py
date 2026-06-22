"""상황 입력(case) 요청/응답 스키마 (SCR-03)."""

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    service_type: str
    policy_ids: list[str]
    disease_kcd: str
    disease_name: str
    is_inpatient: bool = False
    is_outpatient: bool = False
    surgery: bool = False
    admission_days_diagnosed: int | None = None
    admission_days_current: int | None = None
    treatment_items: list[str] = Field(default_factory=list)
    payment_amount: int | None = None
    visit_dates: list[str] = Field(default_factory=list)
    annual_visit_count: int | None = None
    claimed_policy_ids: list[str] = Field(default_factory=list)
    policy_elapsed_days: int | None = None  # None → 면책·감액 "확인 불가"


class CaseCreated(BaseModel):
    case_id: str
