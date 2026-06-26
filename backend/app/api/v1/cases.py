"""상황 입력·이력 라우트 (v2.1)."""

from flask import g, request
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

from app.auth import require_auth
from app.core import response
from app.core.errors import ForbiddenError, NotFoundError
from app.schemas.case import (
    AnswersRequest,
    AnswersResponse,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseListItem,
    CasePath,
    DashboardPatchRequest,
    DashboardPatchResponse,
    DashboardResponse,
    ExtractedInfoPatchRequest,
    ExtractedInfoPatchResponse,
    MedicalDetailResponse,
    MedicalStatementUploadForm,
    PaymentResponse,
    PaymentTextRequest,
)
from app.schemas.common import ERRORS_OWNERSHIP, Envelope
from app.services import case_service

# 본인 데이터 접근 도메인 — 검증/인증/소유권/미존재/서버오류는 블루프린트 공통.
# 각 라우트는 성공 응답만 명시한다.
bp = APIBlueprint(
    "cases",
    __name__,
    url_prefix="/api/v1",
    abp_tags=[Tag(name="cases")],
    abp_security=[{"jwt": []}],
    abp_responses=ERRORS_OWNERSHIP,
)


@bp.post("/cases", responses={201: Envelope[CaseCreateResponse]})
@require_auth
def create_case(body: CaseCreateRequest):
    """최초 상황 입력 및 분석 세션 시작 (v2.1)."""
    try:
        if not body.service_type or not body.policy_ids or not body.initial_situation:
            return response.fail(
                "validation_error", "필수 항목(service_type, policy_ids, initial_situation)이 누락되었습니다.", 400
            )

        data = case_service.create_case(g.user_id, body.service_type, body.policy_ids, body.initial_situation)
        return response.ok(data, 201)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/payment", responses={200: Envelope[PaymentResponse]})
@require_auth
def save_payment(path: CasePath, body: PaymentTextRequest):
    """결제 문자/카드내역 입력 및 추출 (v2.1)."""
    try:
        case_id = path.case_id
        data = case_service.save_payment(g.user_id, case_id, body.payment_text)
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/medical-detail-statement", responses={200: Envelope[MedicalDetailResponse]})
@require_auth
def save_medical_detail_statement(path: CasePath, form: MedicalStatementUploadForm):
    """진료비 세부산정내역서 업로드 및 추출 — PDF 또는 사진(JPEG/PNG) (v2.1)."""
    try:
        case_id = path.case_id
        if "file" not in request.files:
            return response.fail("validation_error", "파일이 첨부되지 않았습니다.", 400)

        file = request.files["file"]
        file_bytes = file.read()
        if not file_bytes:
            return response.fail("validation_error", "빈 파일은 업로드할 수 없습니다.", 400)

        data = case_service.save_medical_detail_statement(g.user_id, case_id, file_bytes)
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.patch("/cases/<string:case_id>/extracted-info", responses={200: Envelope[ExtractedInfoPatchResponse]})
@require_auth
def patch_extracted_info(path: CasePath, body: ExtractedInfoPatchRequest):
    """추출된 결제/진료 정보 직접 확인 및 수정 (v2.1)."""
    try:
        case_id = path.case_id
        info = body.model_dump(exclude_unset=True)
        data = case_service.patch_extracted_info(g.user_id, case_id, info)
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/cases/<string:case_id>/answers", responses={200: Envelope[AnswersResponse]})
@require_auth
def save_answers(path: CasePath, body: AnswersRequest):
    """부족 정보에 대한 추가 답변 저장 (v2.1)."""
    try:
        case_id = path.case_id
        answers = [answer.model_dump() for answer in body.answers]
        data = case_service.save_answers(g.user_id, case_id, answers)
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/cases/<string:case_id>/dashboard", responses={200: Envelope[DashboardResponse]})
@require_auth
def get_dashboard(path: CasePath):
    """대시보드 화면 9개 항목 조회 (v2.1 신규)."""
    try:
        case_id = path.case_id
        data = case_service.get_dashboard(g.user_id, case_id)
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.patch("/cases/<string:case_id>/dashboard", responses={200: Envelope[DashboardPatchResponse]})
@require_auth
def patch_dashboard(path: CasePath, body: DashboardPatchRequest):
    """대시보드 화면 9개 항목 직접 수정 및 저장 (v2.1 신규)."""
    try:
        case_id = path.case_id
        data = case_service.patch_dashboard(g.user_id, case_id, body.model_dump(exclude_unset=True))
        return response.ok(data)
    except ValueError as val_err:
        return response.fail("validation_error", str(val_err), 400)
    except ForbiddenError as fb_err:
        return response.fail("forbidden", str(fb_err), 403)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return response.fail("server_error", str(e), 500)


@bp.get("/cases/my", responses={200: Envelope[list[CaseListItem]]})
@require_auth
def get_my_cases():
    """내 분석 이력 목록 조회 (F-05)."""
    data = case_service.get_my_cases(g.user_id)
    return response.ok(data)
