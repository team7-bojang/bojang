from flask import g, request
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.auth import require_auth
from app.core import response
from app.services import policy_service

bp = APIBlueprint("policies", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="policies")])


# 요청/응답용 임시 Pydantic 모델 정의 (flask-openapi3 자동 문서화용)
class SelectPresetRequest(BaseModel):
    preset_ids: list[str]


class PolicyPath(BaseModel):
    id: str = Field(..., description="보험 상품 ID (UUID)")


class SourceQuery(BaseModel):
    page: int = Field(default=1, description="약관 원문 페이지 번호")


@bp.get("/policies/presets")
def get_presets():
    """선탑재 상품 목록 조회 (SCR-01)."""
    try:
        data = policy_service.get_presets()
        return response.ok({"presets": data})
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/policies/select", security=[{"jwt": []}])
@require_auth
def select_presets(body: SelectPresetRequest):
    """선탑재 상품 등록 (SCR-01)."""
    try:
        if not body.preset_ids:
            return response.fail("validation_error", "preset_ids가 빈 배열입니다.", 400)
        
        from app.core.errors import NotFoundError
        policy_ids = policy_service.select_presets(g.user_id, body.preset_ids)
        return response.ok({"registered_policy_ids": policy_ids}, 201)
    except NotFoundError as nf_err:
        return response.fail("not_found", str(nf_err), 404)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.post("/policies/upload", security=[{"jwt": []}])
@require_auth
def upload_policy():
    """약관 PDF 업로드 및 분석 (SCR-02)."""
    try:
        if "file" not in request.files:
            return response.fail("validation_error", "파일이 첨부되지 않았습니다.", 400)

        file = request.files["file"]
        if file.filename == "":
            return response.fail("validation_error", "파일명이 유효하지 않습니다.", 400)

        data = policy_service.upload_pdf(g.user_id, file.filename)
        return response.ok(data, 201)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/policies/my", security=[{"jwt": []}])
@require_auth
def get_my_policies():
    """내 보험·특약 목록 조회 (SCR-01)."""
    try:
        data = policy_service.get_my_policies(g.user_id)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/policies/<string:id>/source")
def get_policy_source(path: PolicyPath, query: SourceQuery):
    """약관 원문 조회 (SCR-02)."""
    try:
        policy_id = path.id
        data = policy_service.get_source(policy_id, query.page)
        return response.ok(data)
    except Exception as e:
        return response.fail("not_found", str(e), 404)
