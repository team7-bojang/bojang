"""보장 탐색·비교 라우트 (SCR-04·05, 데모의 심장).

  POST /analysis/search    보장 교차 검색 (F-02)
  POST /analysis/compare   조건별 비교 (F-03)

※ search 는 flask-openapi3 배선 패턴 예시(요청/응답 스키마 지정 → 자동 문서화)다.
  나머지 라우트도 동일 패턴으로 service 연결 시 채운다.
"""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

from app.core.response import fail
from app.schemas.analysis import SearchRequest, SearchResponse

bp = APIBlueprint("analysis", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="analysis")])


@bp.post("/analysis/search", responses={200: SearchResponse})
def search(body: SearchRequest):
    # TODO(조윤): analysis_service.search(body.case_id)
    #   retrieve(rag) → judge(룰엔진) → explain(rag) → 인용검증(rag.citation)
    return fail("not_implemented", "탐색 미구현", 501)
