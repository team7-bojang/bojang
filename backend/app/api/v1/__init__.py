"""API v1 라우트 등록 지점 (flask-openapi3).

도메인별 APIBlueprint 를 등록한다. 각 블루프린트가 url_prefix="/api/v1" 를 갖고,
pydantic 스키마로 정의된 라우트는 /openapi/swagger 에 자동 반영된다 (설계서 §4).
새 도메인 라우트를 추가하면 _DOMAIN_BLUEPRINTS 에 등록한다.
"""

from flask_openapi3.openapi import OpenAPI

from app.api.v1.analysis import bp as analysis_bp
from app.api.v1.cases import bp as cases_bp
from app.api.v1.diseases import bp as diseases_bp
from app.api.v1.health import bp as health_bp
from app.api.v1.policies import bp as policies_bp
from app.api.v1.reports import bp as reports_bp

_DOMAIN_BLUEPRINTS = (
    policies_bp,
    diseases_bp,
    cases_bp,
    analysis_bp,
    reports_bp,
)


def register_v1(app: OpenAPI) -> None:
    app.register_api(health_bp)  # /health (버전 무관)
    for bp in _DOMAIN_BLUEPRINTS:
        app.register_api(bp)  # 각 bp 가 url_prefix="/api/v1" 보유
