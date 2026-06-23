"""보장 탐색·비교 라우트 (SCR-04·05, 데모의 심장).

POST /analysis/search    보장 교차 검색 (F-02)
POST /analysis/compare   조건별 비교 (F-03)
"""

from flask import g
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

from app.auth import require_auth
from app.core import response
from app.schemas.analysis import CompareRequest, SearchRequest
from app.services import analysis_service

bp = APIBlueprint(
    "analysis", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="analysis")], abp_security=[{"jwt": []}]
)


@bp.post("/analysis/search")
@require_auth
def search_analysis(body: SearchRequest):
    """상황 기준 보장 교차 검색 (RAG + 룰 엔진 연동) (SCR-04)."""
    data = analysis_service.search_analysis(g.user_id, body.case_id)
    return response.ok(data)


@bp.post("/analysis/compare")
@require_auth
def compare_scenarios(body: CompareRequest):
    """조건별 비교 분석 (v2.1)."""
    try:
        scenarios_list = [sc.model_dump() for sc in body.scenarios]
        data = analysis_service.compare_scenarios(
            g.user_id, body.case_id, scenarios_list
        )
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
