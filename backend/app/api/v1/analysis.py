"""보장 탐색·비교 라우트 (SCR-04·05, 데모의 심장).

  POST /analysis/search    보장 교차 검색 (F-02)
  POST /analysis/compare   조건별 비교 (F-03)

※ search 는 flask-openapi3 배선 패턴 예시(요청/응답 스키마 지정 → 자동 문서화)다.
  나머지 라우트도 동일 패턴으로 service 연결 시 채운다.
"""

from flask import g
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel

from app.auth import require_auth
from app.core import response
from app.services import analysis_service

bp = APIBlueprint("analysis", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="analysis")])


# 요청용 Pydantic 모델
class SearchRequest(BaseModel):
    case_id: str


class CompareRequest(BaseModel):
    case_id: str
    scenarios: list[dict]


@bp.post("/analysis/search")
@require_auth
def search_analysis(body: SearchRequest):
    """상황 기준 보장 교차 검색 (RAG + 룰 엔진 연동) (SCR-04)."""
    data = analysis_service.search_analysis(g.user_id, body.case_id)
    return response.ok(data)


@bp.post("/analysis/compare")
@require_auth
def compare_scenarios(body: CompareRequest):
    """조건별 비교 분석 (SCR-05)."""
    data = analysis_service.compare_scenarios(g.user_id, body.case_id, body.scenarios)
    return response.ok(data)
