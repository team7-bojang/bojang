"""리포트 라우트 (SCR-06, F-04).

POST /reports         리포트 생성
GET  /reports/<id>    리포트 조회
"""

from flask import g, request
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel

from app.auth import require_auth
from app.core import response
from app.services import report_service

bp = APIBlueprint("reports", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="reports")], abp_security=[{"jwt": []}])


class ReportCreateRequest(BaseModel):
    case_id: str


@bp.post("/reports")
@require_auth
def create_report(body: ReportCreateRequest):
    """리포트 생성 (SCR-06)."""
    try:
        data = report_service.create_report(g.user_id, body.case_id)
        return response.ok(data, 201)
    except Exception as e:
        return response.fail("server_error", str(e), 500)


@bp.get("/reports/<string:id>")
@require_auth
def get_report():
    """리포트 상세 조회 (SCR-06)."""
    try:
        report_id = request.view_args.get("id")
        data = report_service.get_report(report_id)
        return response.ok(data)
    except Exception as e:
        return response.fail("not_found", str(e), 404)
