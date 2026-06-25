"""상황 입력(case) 요청/응답 스키마 (v2.1)."""

from typing import Any

from pydantic import BaseModel, Field


# ── Path 파라미터 ──
class CasePath(BaseModel):
    case_id: str = Field(..., description="케이스 UUID")


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


# ── POST /cases/{case_id}/answers (API 10) ──
class AnswerItem(BaseModel):
    question_id: str = Field(..., description="답변 대상 질문 ID")
    value: Any = Field(..., description="답변 값")


class AnswersRequest(BaseModel):
    answers: list[AnswerItem] = Field(default_factory=list, description="추가 답변 목록")


# ── POST /cases/{case_id}/medical-detail-statement (API 9) ──
class MedicalStatementUploadForm(BaseModel):
    # format="binary" → Swagger에서 파일 선택 버튼 표시 (app/api/v1/policies.py::UploadForm 과 동일 패턴).
    # required(...)로 두면 누락 시 flask-openapi3 가 응답 봉투(ok/fail)를 건너뛰고 raw 422를 반환하므로
    # optional 로 두고, 누락 검증은 라우트 본문에서 response.fail() 로 직접 처리한다.
    file: Any = Field(
        default=None,
        json_schema_extra={"type": "string", "format": "binary"},
        description="진료비 세부산정내역서 파일 (PDF 또는 사진 JPEG/PNG)",
    )


class MedicalItemDetail(BaseModel):
    name: str
    amount: int
    is_non_covered: bool
    count: int


class ExtractedMedicalInfo(BaseModel):
    disease_name: str | None = None
    disease_kcd: str | None = None
    hospital_name: str | None = None
    visit_dates: list[str] = []
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
