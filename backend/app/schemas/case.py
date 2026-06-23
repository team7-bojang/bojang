"""상황 입력(case) 요청/응답 스키마 (v2.1)."""

from pydantic import BaseModel, Field


# ── POST /cases (API 7) ──
class CaseCreateRequest(BaseModel):
    service_type: str = Field(..., description="CASE1 / CASE2 구분")
    policy_ids: list[str] = Field(..., description="선택한 보험 ID 목록")
    initial_situation: str = Field(..., description="최초 상황 텍스트")


class CaseCreateResponse(BaseModel):
    case_id: str
    service_type: str
    policy_ids: list[str]
    initial_situation: str
    claim_status: str
    disease_name: str | None = None
    disease_kcd: str | None = None
    recommended_input_method: str | None = None
    available_input_methods: list[str]
    message: str | None = None


# ── POST /cases/{case_id}/payment (API 8) ──
class PaymentTextRequest(BaseModel):
    input_method: str = Field(default="PAYMENT")
    payment_text: str = Field(..., description="결제 텍스트")


class ExtractedPayment(BaseModel):
    payment_amount: int
    payment_date: str
    hospital_name: str


class VisitTypeInference(BaseModel):
    inferred: bool
    inferred_is_inpatient: bool | None = None
    inferred_is_outpatient: bool | None = None
    message: str | None = None
    threshold_basis: str | None = None


class PaymentResponse(BaseModel):
    case_id: str
    input_method: str
    extracted_payment: ExtractedPayment
    needs_confirmation: bool
    visit_type_inference: VisitTypeInference


# ── POST /cases/{case_id}/medical-detail-statement (API 9) ──
class MedicalItemDetail(BaseModel):
    name: str
    amount: int
    is_non_covered: bool
    count: int


class ExtractedMedicalInfo(BaseModel):
    disease_name: str | None = None
    disease_kcd: str | None = None
    hospital_name: str | None = None
    visit_date: str | None = None
    is_inpatient: bool
    is_outpatient: bool
    surgery: bool
    treatment_items: list[str]
    payment_amount: int | None = None
    total_amount: int | None = None
    patient_paid_amount: int | None = None
    nhis_paid_amount: int | None = None
    non_covered_amount: int | None = None
    item_details: list[MedicalItemDetail] = []


class MedicalDetailResponse(BaseModel):
    case_id: str
    input_method: str
    extracted_medical_info: ExtractedMedicalInfo
    needs_confirmation: bool
