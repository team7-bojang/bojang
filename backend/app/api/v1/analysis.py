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


@bp.post("/analysis/judge")
@require_auth
def judge_analysis(body: SearchRequest):
    """상황 기준 보장 판정 (RAG/LLM/스냅샷을 생략한 룰 엔진 고속 판정) (SCR-04).

    body.coverage_amounts 가 전달되면 DB 저장 없이 그 가입금액으로 정액 예상 보험금을 재계산한다.
    body.patient_paid_amount/non_covered_amount 가 전달되면 실손 covered_amount 로 재계산한다.
    """
    coverage_amounts = [c.model_dump() for c in body.coverage_amounts] if body.coverage_amounts is not None else None
    data = analysis_service.judge_analysis(
        g.user_id,
        body.case_id,
        coverage_amounts,
        patient_paid_amount=body.patient_paid_amount,
        non_covered_amount=body.non_covered_amount,
    )
    return response.ok(data)


@bp.post("/analysis/compare")
@require_auth
def compare_scenarios(body: CompareRequest):
    """조건별 비교 분석.

    scenarios(v2.1 다중 시나리오)가 오면 그 형식으로, 없으면 current_days/target_days(옛 형식)로 분기한다.
    """
    try:
        if body.scenarios is not None:
            scenarios_list = [sc.model_dump() for sc in body.scenarios]
            data = analysis_service.compare_scenarios(g.user_id, body.case_id, scenarios_list)
        else:
            data = analysis_service.compare_scenarios(
                g.user_id,
                body.case_id,
                current_days=body.current_days,
                target_days=body.target_days,
            )
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
