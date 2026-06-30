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

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "service_type": "CASE2",
                "policy_ids": ["3f2a1b5c-1111-2222-3333-444455556666"],
                "initial_situation": "뇌경색으로 5일 입원해서 치료받았어요.",
                "claim_status": "NEW",
                "disease_name": "뇌경색증",
                "disease_kcd": "I63",
                "recommended_input_method": "MEDICAL_DETAIL_STATEMENT",
                "available_input_methods": ["PAYMENT", "MEDICAL_DETAIL_STATEMENT"],
                "message": "결제 정보 또는 진료비 세부산정내역서를 입력해 주세요.",
            }
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "input_method": "PAYMENT",
                "extracted_payment": {
                    "payment_amount": 320000,
                    "payment_date": "2026-06-20",
                    "hospital_name": "서울대학교병원",
                },
                "needs_confirmation": True,
                "visit_type_inference": {
                    "inferred": True,
                    "inferred_is_inpatient": True,
                    "inferred_is_outpatient": False,
                    "message": "결제 금액 기준으로 입원으로 추정됩니다.",
                    "threshold_basis": "30만원 이상",
                },
            }
        }
    }


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
    full_self_pay_amount: int | None = None
    non_covered_amount: int | None = None
    item_details: list[MedicalItemDetail] = []


class MedicalDetailResponse(BaseModel):
    case_id: str
    input_method: str
    extracted_medical_info: ExtractedMedicalInfo
    needs_confirmation: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "input_method": "MEDICAL_DETAIL_STATEMENT",
                "extracted_medical_info": {
                    "disease_name": "뇌경색증",
                    "disease_kcd": "I63",
                    "hospital_name": "서울대학교병원",
                    "visit_dates": ["2026-06-16", "2026-06-20"],
                    "is_inpatient": True,
                    "is_outpatient": False,
                    "surgery": False,
                    "treatment_items": ["MRI_MRA", "EMERGENCY"],
                    "payment_amount": 320000,
                    "total_amount": 1850000,
                    "patient_paid_amount": 320000,
                    "nhis_paid_amount": 1530000,
                    "full_self_pay_amount": 120000,
                    "non_covered_amount": 200000,
                    "item_details": [{"name": "MRI", "amount": 180000, "is_non_covered": True, "count": 1}],
                },
                "needs_confirmation": True,
            }
        }
    }


# ── PATCH /cases/{case_id}/extracted-info (API 11) ──
class ExtractedInfoPatchRequest(BaseModel):
    """추출 정보 직접 수정 요청. 전달된 필드만 부분 갱신된다."""

    input_method: str | None = Field(default=None, description="PAYMENT / MEDICAL_DETAIL_STATEMENT")
    disease_name: str | None = None
    disease_kcd: str | None = None
    surgery: bool | None = None
    confirmed_is_inpatient: bool | None = None
    confirmed_is_outpatient: bool | None = None
    policy_elapsed_days: int | None = None
    current_days: int | None = None
    diag_days: int | None = None
    claimed_policy_ids: list[str] | None = None
    treatment_items: list[str] | None = None
    payment_amount: int | None = None
    coverage_amounts: list[dict[str, Any]] | None = Field(
        default=None, description="보장별 가입금액 [{rider_id, amount, amount_source}]"
    )
    confirmed_payment: dict[str, Any] | None = None
    confirmed_medical_info: dict[str, Any] | None = None


# 부분 갱신/답변 응답의 freeform `case` 예시 (cases 테이블 행 일부).
_CASE_ROW_EXAMPLE = {
    "id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
    "service_type": "CASE2",
    "disease_name": "뇌경색증",
    "disease_kcd": "I63",
    "is_inpatient": True,
    "is_outpatient": False,
    "surgery": False,
    "treatment_items": ["MRI_MRA", "EMERGENCY"],
    "admission_days_current": 5,
    "payment_amount": 320000,
}


class ExtractedInfoPatchResponse(BaseModel):
    case_id: str
    ready_for_dashboard: bool
    case: dict[str, Any]
    treatment_types: list[dict[str, Any]] = []
    next_question: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "ready_for_dashboard": True,
                "case": _CASE_ROW_EXAMPLE,
                "treatment_types": [{"code": "MRI_MRA", "label": "MRI/MRA 검사"}],
                "next_question": None,
            }
        }
    }


# ── POST /cases/{case_id}/answers 응답 (API 10) ──
class AnswersResponse(BaseModel):
    case_id: str
    ready_for_dashboard: bool
    case: dict[str, Any]
    treatment_types: list[dict[str, Any]] = []
    next_question: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "ready_for_dashboard": True,
                "case": _CASE_ROW_EXAMPLE,
                "treatment_types": [{"code": "MRI_MRA", "label": "MRI/MRA 검사"}],
                "next_question": {
                    "question_id": "admission_days_diagnosed",
                    "text": "진단 시점 기준 입원일수를 입력해 주세요.",
                },
            }
        }
    }


# ── 대시보드 (API 12/13) ──
_DASHBOARD_EXAMPLE = {
    "disease_name": "뇌경색증",
    "disease_kcd": "I63",
    "disease_kcd_candidates": ["I63", "I63.9"],
    "is_inpatient": True,
    "is_outpatient": False,
    "admission_days_current": 5,
    "admission_days_diagnosed": 5,
    "treatment_items": ["MRI_MRA", "EMERGENCY"],
    "payment_amount": 320000,
    "visit_date": "2026-06-16",
    "surgery": False,
    "annual_visit_count": 1,
    "policy_elapsed_days": 800,
}


class DashboardData(BaseModel):
    disease_name: str | None = None
    disease_kcd: str | None = None
    disease_kcd_candidates: list[Any] = []
    is_inpatient: bool
    is_outpatient: bool
    admission_days_current: int | None = None
    admission_days_diagnosed: int | None = None
    treatment_items: list[str] = []
    payment_amount: int | None = None
    visit_date: Any | None = None
    surgery: bool | None = None
    annual_visit_count: int | None = None
    policy_elapsed_days: int | None = None
    patient_paid_amount: int | None = None
    non_covered_amount: int | None = None

    model_config = {"json_schema_extra": {"example": _DASHBOARD_EXAMPLE}}


class DashboardResponse(BaseModel):
    case_id: str
    service_type: str
    dashboard: DashboardData
    policies: list[Any] = []
    display_name: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "service_type": "CASE2",
                "dashboard": _DASHBOARD_EXAMPLE,
            }
        }
    }


class DashboardPatchRequest(BaseModel):
    """대시보드 직접 수정 요청. 전달된 필드만 부분 갱신된다."""

    disease_name: str | None = None
    disease_kcd: str | None = None
    surgery: bool | None = None
    is_inpatient: bool | None = None
    is_outpatient: bool | None = None
    admission_days_current: int | None = None
    admission_days_diagnosed: int | None = None
    treatment_items: list[str] | None = None
    payment_amount: int | None = None
    visit_dates: Any | None = Field(default=None, description="내원일자 (YYYY-MM-DD 또는 그 배열)")
    visit_date: Any | None = None
    annual_visit_count: int | None = None
    policy_elapsed_days: int | None = None
    patient_paid_amount: int | None = None
    non_covered_amount: int | None = None


class DashboardPatchResponse(BaseModel):
    case_id: str
    updated: bool
    dashboard: DashboardData

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "updated": True,
                "dashboard": _DASHBOARD_EXAMPLE,
            }
        }
    }


# ── GET /cases/my (F-05) ──
class CaseListItem(BaseModel):
    case_id: str
    created_at: str
    summary: str
    eligible_count: int
    report_id: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "case_id": "9c1f7e2a-4b3d-4c1a-9f0e-2d6b1a7c8e34",
                "created_at": "2026-06-20T11:05:00+00:00",
                "summary": "뇌경색증 치료 (5일 입원)",
                "eligible_count": 3,
                "report_id": "b7c8e34d-1111-2222-3333-444455556666",
            }
        }
    }
