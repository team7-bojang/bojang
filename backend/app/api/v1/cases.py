"""상황 입력·이력 라우트 (SCR-03·07).

POST /cases                                   최초 상황 입력
POST /cases/{case_id}/payment                결제 내역 입력
POST /cases/{case_id}/medical-detail-statement 진료비 세부산정내역서 업로드
PATCH /cases/{case_id}/extracted-info        추출 정보 수정
POST /cases/{case_id}/answers                추가 답변 저장
GET   /cases/{case_id}/dashboard              대시보드 항목 조회 (4-12)
PATCH /cases/{case_id}/dashboard              대시보드 항목 직접 수정 (4-13)
GET  /cases/my                                내 분석 이력 목록
"""

from flask import g, request
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.auth import require_auth
from app.core import response
from app.services import case_service

bp = APIBlueprint("cases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="cases")])


# 요청용 Pydantic 모델 정의
class InitialSituationRequest(BaseModel):
    service_type: str = Field(description="CASE1 / CASE2")
    policy_ids: list[str] = Field(description="선택한 보험 uuid 목록. CASE1 다중, CASE2 단일")
    initial_situation: str


class PaymentRequest(BaseModel):
    payment_text: str = Field(description="결제 문자 또는 카드 내역 텍스트")


class ExtractedInfoPatch(BaseModel):
    disease_kcd: str | None = None
    disease_name: str | None = None
    is_inpatient: bool | None = None
    is_outpatient: bool | None = None
    surgery: bool | None = None
    admission_days_diagnosed: int | None = None
    admission_days_current: int | None = None
    treatment_items: list[str] | None = None
    payment_amount: int | None = None
    visit_dates: list[str] | None = None
    claimed_policy_ids: list[str] | None = None
    policy_elapsed_days: int | None = None


class AnswerItem(BaseModel):
    question_id: str
    value: bool | int | str | list | None
    selected_label: str | None = None  # policy_elapsed_days 구간 선택 라벨용


class AnswersRequest(BaseModel):
    answers: list[AnswerItem]


class DashboardPatch(BaseModel):
    disease_name: str | None = None
    disease_kcd: str | None = None
    is_inpatient: bool | None = None
    is_outpatient: bool | None = None
    admission_days_diagnosed: int | None = None
    admission_days_current: int | None = None
    treatment_items: list[str] | None = None
    payment_amount: int | None = None
    visit_dates: list[str] | None = None
    surgery: bool | None = None
    annual_visit_count: int | None = None
    policy_elapsed_days: int | None = None


@bp.post("/cases")
@require_auth
def create_case(body: InitialSituationRequest):
    """최초 상황 입력 및 입력 방식 추천 (4-7)."""
    data = case_service.create_case(
        g.user_id,
        body.service_type,
        body.policy_ids,
        body.initial_situation,
    )
    return response.ok(data, 201)


@bp.post("/cases/<string:case_id>/payment")
@require_auth
def save_payment(body: PaymentRequest):
    """결제 문자/카드내역 입력 또는 업로드 (v1.5)."""
    case_id = request.view_args.get("case_id")
    data = case_service.save_payment(g.user_id, case_id, body.payment_text)
    return response.ok(data)


@bp.post("/cases/<string:case_id>/medical-detail-statement")
@require_auth
def save_medical_detail_statement():
    """진료비 세부산정내역서 PDF 업로드 및 추출 (v1.5)."""
    case_id = request.view_args.get("case_id")
    if "file" not in request.files:
        return response.fail("validation_error", "파일이 첨부되지 않았습니다.", 400)

    file = request.files["file"]
    data = case_service.save_medical_detail_statement(g.user_id, case_id, file.filename)
    return response.ok(data)


@bp.patch("/cases/<string:case_id>/extracted-info")
@require_auth
def patch_extracted_info(body: ExtractedInfoPatch):
    """추출된 결제/진료 정보 확인 및 수정 (v1.5)."""
    case_id = request.view_args.get("case_id")
    updates = body.model_dump(exclude_unset=True)
    data = case_service.patch_extracted_info(g.user_id, case_id, updates)
    return response.ok(data)


@bp.post("/cases/<string:case_id>/answers")
@require_auth
def save_answers(body: AnswersRequest):
    """부족 정보에 대한 추가 답변 저장 (4-11)."""
    case_id = request.view_args.get("case_id")
    answers = [a.model_dump() for a in body.answers]
    data = case_service.save_answers(g.user_id, case_id, answers)
    return response.ok(data)


@bp.get("/cases/<string:case_id>/dashboard")
@require_auth
def get_dashboard():
    """대시보드 항목 조회 (4-12)."""
    case_id = request.view_args.get("case_id")
    data = case_service.get_dashboard(g.user_id, case_id)
    return response.ok(data)


@bp.patch("/cases/<string:case_id>/dashboard")
@require_auth
def patch_dashboard(body: DashboardPatch):
    """대시보드 항목 직접 수정 (4-13). 보낸 필드만 갱신한다."""
    case_id = request.view_args.get("case_id")
    updates = body.model_dump(exclude_unset=True)
    data = case_service.patch_dashboard(g.user_id, case_id, updates)
    return response.ok(data)


@bp.get("/cases/my")
@require_auth
def get_my_cases():
    """내 분석 이력 목록 조회 (F-05)."""
    data = case_service.get_my_cases(g.user_id)
    return response.ok(data)
