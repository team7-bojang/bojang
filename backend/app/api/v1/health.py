"""헬스 체크."""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

from app.schemas.health import HealthResponse

bp = APIBlueprint("health", __name__, abp_tags=[Tag(name="health")])


@bp.get("/health", responses={200: HealthResponse})
def health():
    return HealthResponse(status="ok").model_dump()
