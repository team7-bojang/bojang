"""리포트 라우트 (SCR-06, F-04).

POST /reports         리포트 생성
GET  /reports/<id>    리포트 조회
"""

from flask import g
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.auth import require_auth
from app.core import response
from app.schemas.common import ERRORS_AUTH, Envelope, ErrorResponse
from app.schemas.report import Report, ReportCreated
from app.services import report_service

# 인증/서버오류는 공통, 404(미존재) 는 이 도메인 공통. 라우트는 성공 응답만 명시.
bp = APIBlueprint(
    "reports",
    __name__,
    url_prefix="/api/v1",
    abp_tags=[Tag(name="reports")],
    abp_security=[{"jwt": []}],
    abp_responses={**ERRORS_AUTH, 404: ErrorResponse},
)


class ReportCreateRequest(BaseModel):
    case_id: str


class ReportPath(BaseModel):
    id: str = Field(..., description="리포트 ID (UUID)")


@bp.post("/reports", responses={201: Envelope[ReportCreated]})
@require_auth
def create_report(body: ReportCreateRequest):
    """리포트 생성 (SCR-06)."""
    try:
        data = report_service.create_report(g.user_id, body.case_id)
        return response.ok(data, 201)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/reports/<string:id>", responses={200: Envelope[Report]})
@require_auth
def get_report(path: ReportPath):
    """리포트 상세 조회 (SCR-06)."""
    try:
        data = report_service.get_report(path.id)
        return response.ok(data)
    except Exception as e:
        return response.fail("not_found", str(e), 404)
