"""상황 입력·이력 라우트 (SCR-03·07).

POST /cases                                   최초 상황 입력
POST /cases/{case_id}/payment                결제 내역 입력
POST /cases/{case_id}/medical-detail-statement 진료비 세부산정내역서 업로드
PATCH /cases/{case_id}/extracted-info        추출 정보 수정
POST /cases/{case_id}/answers                추가 답변 저장
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
    initial_situation: str


class PaymentRequest(BaseModel):
    payment_text: str = Field(description="결제 문자 또는 카드 내역 텍스트")


class ExtractedInfoPatch(BaseModel):
    disease_kcd: str | None = None
    disease_name: str | None = None
    surgery: bool | None = None
    diag_days: int | None = None
    current_days: int | None = None
    claimed_policy_ids: list[str] | None = None
    policy_elapsed_days: int | None = None


class AnswersRequest(BaseModel):
    surgery: bool | None = None
    current_days: int | None = None
    diag_days: int | None = None


@bp.post("/cases")
@require_auth
def create_case(body: InitialSituationRequest):
    """최초 상황 입력 및 입력 방식 추천 (v1.5)."""
    try:
        data = case_service.create_case(g.user_id, body.initial_situation)
        return response.ok(data, 201)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/payment")
@require_auth
def save_payment(body: PaymentRequest):
    """결제 문자/카드내역 입력 또는 업로드 (v1.5)."""
    try:
        case_id = request.view_args.get("case_id")
        data = case_service.save_payment(g.user_id, case_id, body.payment_text)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/medical-detail-statement")
@require_auth
def save_medical_detail_statement():
    """진료비 세부산정내역서 PDF 업로드 및 추출 (v1.5)."""
    try:
        case_id = request.view_args.get("case_id")
        if "file" not in request.files:
            return response.fail("validation_error", "파일이 첨부되지 않았습니다.", 400)

        file = request.files["file"]
        data = case_service.save_medical_detail_statement(g.user_id, case_id, file.filename)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.patch("/cases/<string:case_id>/extracted-info")
@require_auth
def patch_extracted_info(body: ExtractedInfoPatch):
    """추출된 결제/진료 정보 확인 및 수정 (v1.5)."""
    try:
        case_id = request.view_args.get("case_id")
        data = case_service.patch_extracted_info(g.user_id, case_id, body.model_dump())
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/answers")
@require_auth
def save_answers(body: AnswersRequest):
    """부족 정보에 대한 추가 답변 저장 (v1.5)."""
    try:
        case_id = request.view_args.get("case_id")
        data = case_service.save_answers(g.user_id, case_id, body.model_dump())
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/cases/my")
@require_auth
def get_my_cases():
    """내 분석 이력 목록 조회 (F-05)."""
    try:
        data = case_service.get_my_cases(g.user_id)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
