"""앱 팩토리 — flask-openapi3 기반.

OpenAPI 앱을 쓰면 pydantic 스키마로 정의한 라우트가 자동으로 문서화되고,
Swagger UI 가 같은 앱에서 서빙된다 (배포 시 백엔드와 함께 자동 노출):
    /openapi/swagger   · /openapi/redoc · /openapi/scalar
    /openapi/openapi.json  (프론트 openapi-typescript 입력)
"""

from flask_cors import CORS
from flask_openapi3 import SecurityScheme
from flask_openapi3.models.info import Info
from flask_openapi3.openapi import OpenAPI

from app.api.v1 import register_v1
from app.config import settings

_info = Info(title="AI 보험 보장 분석 API", version="1.0.0")

# Swagger Authorize 버튼용 Bearer 스킴. 보호 라우트는 security=[{"jwt": []}] 로 참조한다.
# (실제 검증은 app/auth/middleware.py::require_auth 가 수행 — 이 선언은 문서/UI 용)
_security_schemes = {"jwt": SecurityScheme(type="http", scheme="bearer", bearerFormat="JWT")}


def create_app() -> OpenAPI:
    """OpenAPI(=Flask 서브클래스) 애플리케이션을 생성·구성한다."""
    app = OpenAPI(__name__, info=_info, security_schemes=_security_schemes)
    app.config["JSON_AS_ASCII"] = False  # 한글 응답 그대로 직렬화

    CORS(app, origins=settings.cors_origins)

    register_v1(app)  # /api/v1/* 도메인 라우트 + /health

    return app
