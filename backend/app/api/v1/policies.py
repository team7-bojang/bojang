from typing import Any

from flask import g, request
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.auth import require_auth
from app.core import response
from app.core.errors import ForbiddenError, NotFoundError
from app.schemas.common import Envelope, ErrorResponse
from app.schemas.policy import PolicyPreset, PolicyWithRiders
from app.schemas.rider import Rider
from app.services import policy_service, user_policy_service

bp = APIBlueprint(
    "policies",
    __name__,
    url_prefix="/api/v1",
    abp_tags=[Tag(name="policies")],
    abp_security=[{"jwt": []}],
)


class SelectPresetRequest(BaseModel):
    preset_ids: list[str]


class PolicyPath(BaseModel):
    id: str = Field(..., description="보험 상품 ID (UUID)")


class SourceQuery(BaseModel):
    page: int = Field(default=1, description="약관 원문 페이지 번호")


class UploadForm(BaseModel):
    # format="binary" → Swagger에서 파일 선택 버튼 표시
    file: Any = Field(
        ...,
        json_schema_extra={"type": "string", "format": "binary"},
        description="약관 PDF 파일 (최대 50MB, 텍스트 레이어 필요)",
    )


class PresetsResponse(BaseModel):
    presets: list[PolicyPreset]

    model_config = {
        "json_schema_extra": {
            "example": {
                "presets": [
                    {
                        "id": "3f2a1b5c-1111-2222-3333-444455556666",
                        "name": "무배당 건강보험",
                        "insurer": "삼성생명",
                        "type": "질병",
                    },
                    {
                        "id": "7d9e2c4a-5555-6666-7777-888899990000",
                        "name": "굿앤굿실손의료비",
                        "insurer": "현대해상",
                        "type": "실손",
                    },
                ]
            }
        }
    }


class SelectPresetsResponse(BaseModel):
    registered_policy_ids: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "registered_policy_ids": [
                    "3f2a1b5c-1111-2222-3333-444455556666",
                    "7d9e2c4a-5555-6666-7777-888899990000",
                ]
            }
        }
    }


class UploadPolicyResponse(BaseModel):
    policy_id: str
    page_count: int

    model_config = {
        "json_schema_extra": {"example": {"policy_id": "c1d2e3f4-9999-0000-1111-222233334444", "page_count": 84}}
    }


class ParseRidersResponse(BaseModel):
    riders: list[Rider]

    model_config = {
        "json_schema_extra": {
            "example": {
                "riders": [
                    {
                        "id": "8b7c0d1e-aaaa-bbbb-cccc-ddddeeeeffff",
                        "name": "뇌혈관질환 진단비 특약",
                        "is_main": False,
                        "trigger_type": "diagnosis",
                        "unit_amount": 20000000,
                        "unit_type": "fixed",
                        "waiting_period_days": 90,
                        "claim_rule": None,
                        "source_pages": [12, 13],
                        "verified": False,
                    }
                ]
            }
        }
    }


class PolicySourceResponse(BaseModel):
    page: int
    text: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 12,
                "text": "제3조(보험금의 지급사유) 회사는 피보험자가 보험기간 중 뇌혈관질환으로 진단확정된 경우...",
            }
        }
    }


class ParseRequest(BaseModel):
    disease_kcd: str = Field(..., description="KCD 코드. 예: I63")
    disease_name: str = Field(default="", description="질병명. 예: 뇌경색증")
    treatment_items: list[str] = Field(
        default_factory=list,
        description='처치 코드 목록. 예: ["MRI_MRA", "EMERGENCY", "CAST"]',
    )
    visit_type: str | None = Field(
        default=None,
        description="내원 유형. INPATIENT / OUTPATIENT / EMERGENCY",
    )
    surgery: bool | None = Field(default=None, description="수술 여부")


@bp.get(
    "/policies/presets",
    responses={200: Envelope[PresetsResponse], 401: ErrorResponse, 500: ErrorResponse},
)
@require_auth
def get_presets():
    """선탑재 상품 목록 조회."""
    try:
        data = policy_service.get_presets()
        return response.ok({"presets": data})
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post(
    "/policies/select",
    responses={
        201: Envelope[SelectPresetsResponse],
        400: ErrorResponse,
        401: ErrorResponse,
        404: ErrorResponse,
        500: ErrorResponse,
    },
)
@require_auth
def select_presets(body: SelectPresetRequest):
    """선탑재 상품 등록."""
    try:
        if not body.preset_ids:
            return response.fail("validation_error", "preset_ids가 빈 배열입니다.", 400)

        policy_ids = policy_service.select_presets(g.user_id, body.preset_ids)
        return response.ok({"registered_policy_ids": policy_ids}, 201)

    except NotFoundError as e:
        return response.fail("not_found", str(e), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post(
    "/policies/upload",
    responses={
        201: Envelope[UploadPolicyResponse],
        400: ErrorResponse,
        401: ErrorResponse,
        500: ErrorResponse,
    },
)
@require_auth
def upload_policy(form: UploadForm):
    """사용자 약관 PDF 업로드 — 텍스트 추출 후 policy_pages 저장."""
    try:
        file = request.files.get("file")
        if not file:
            return response.fail("validation_error", "파일이 첨부되지 않았습니다.", 400)

        if not file.filename:
            return response.fail("validation_error", "파일명이 유효하지 않습니다.", 400)

        if not file.filename.lower().endswith(".pdf"):
            return response.fail("validation_error", "PDF 파일만 업로드 가능합니다.", 400)

        pdf_bytes = file.read()

        data = user_policy_service.upload_pdf(
            user_id=g.user_id,
            file_name=file.filename,
            pdf_bytes=pdf_bytes,
        )

        return response.ok(data, 201)

    except ValueError as e:
        return response.fail("validation_error", str(e), 400)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post(
    "/policies/<string:id>/parse",
    responses={
        200: Envelope[ParseRidersResponse],
        401: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        422: ErrorResponse,
        500: ErrorResponse,
    },
)
@require_auth
def parse_policy_on_demand(path: PolicyPath, body: ParseRequest):
    """업로드 약관 온디맨드 파싱 — 질병/처치 조건 기준으로 관련 특약 추출."""
    try:
        riders = user_policy_service.get_or_parse_riders(
            user_id=g.user_id,
            policy_id=path.id,
            disease_kcd=body.disease_kcd,
            disease_name=body.disease_name,
            treatment_items=body.treatment_items,
            visit_type=body.visit_type,
            surgery=body.surgery,
        )

        return response.ok({"riders": riders})

    except ForbiddenError as e:
        return response.fail("forbidden", str(e), 403)
    except NotFoundError as e:
        return response.fail("not_found", str(e), 404)
    except ValueError as e:
        return response.fail("parse_failed", str(e), 422)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get(
    "/policies/my",
    responses={200: Envelope[list[PolicyWithRiders]], 401: ErrorResponse, 500: ErrorResponse},
)
@require_auth
def get_my_policies():
    """내 보험·특약 목록 조회."""
    try:
        data = policy_service.get_my_policies(g.user_id)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get(
    "/policies/<string:id>/source",
    responses={
        200: Envelope[PolicySourceResponse],
        401: ErrorResponse,
        403: ErrorResponse,
        404: ErrorResponse,
        500: ErrorResponse,
    },
)
@require_auth
def get_policy_source(path: PolicyPath, query: SourceQuery):
    """약관 원문 조회.

    선탑재 약관은 인증 유저 접근 허용.
    사용자 업로드 약관은 소유자만 접근 가능.
    """
    try:
        data = policy_service.get_source(path.id, query.page, g.user_id)
        return response.ok(data)

    except ForbiddenError as e:
        return response.fail("forbidden", str(e), 403)
    except NotFoundError as e:
        return response.fail("not_found", str(e), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
