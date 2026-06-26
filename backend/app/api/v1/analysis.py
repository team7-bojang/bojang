"""보장 탐색·비교 라우트 (SCR-04·05, 데모의 심장).

POST /analysis/search    보장 교차 검색 (F-02)
POST /analysis/compare   조건별 비교 (F-03)
"""

from flask import g
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

from app.auth import require_auth
from app.core import response
from app.schemas.analysis import CompareRequest, CompareResponse, SearchRequest, SearchResponse
from app.schemas.common import ERRORS_AUTH, Envelope
from app.services import analysis_service

# 인증/서버오류는 블루프린트 공통. 라우트는 성공 응답만 명시.
bp = APIBlueprint(
    "analysis",
    __name__,
    url_prefix="/api/v1",
    abp_tags=[Tag(name="analysis")],
    abp_security=[{"jwt": []}],
    abp_responses=ERRORS_AUTH,
)


@bp.post("/analysis/search", responses={200: Envelope[SearchResponse]})
@require_auth
def search_analysis(body: SearchRequest):
    """상황 기준 보장 교차 검색 (RAG + 룰 엔진 연동) (SCR-04)."""
    data = analysis_service.search_analysis(g.user_id, body.case_id)
    return response.ok(data)


@bp.post("/analysis/judge", responses={200: Envelope[SearchResponse]})
@require_auth
def judge_analysis(body: SearchRequest):
    """상황 기준 보장 판정 (RAG/LLM/스냅샷을 생략한 룰 엔진 고속 판정) (SCR-04).

    body.coverage_amounts 가 전달되면 DB 저장 없이 그 가입금액으로 예상 보험금을 재계산한다.
    """
    coverage_amounts = [c.model_dump() for c in body.coverage_amounts] if body.coverage_amounts is not None else None
    data = analysis_service.judge_analysis(g.user_id, body.case_id, coverage_amounts)
    return response.ok(data)


@bp.post("/analysis/compare", responses={200: Envelope[CompareResponse]})
@require_auth
def compare_scenarios(body: CompareRequest):
    """조건별 비교 분석 (v2.1)."""
    try:
        scenarios_list = [sc.model_dump() for sc in body.scenarios]
        data = analysis_service.compare_scenarios(
            g.user_id,
            body.case_id,
            scenarios_list,
            coverage_amounts=body.coverage_amounts,
            covered_amounts=body.covered_amounts,
            patient_paid_amount=body.patient_paid_amount,
            non_covered_amount=body.non_covered_amount,
        )
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
