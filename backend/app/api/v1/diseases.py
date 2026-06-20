from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.core import response
from app.services import disease_service

bp = APIBlueprint("diseases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="diseases")])


class DiseaseSearchQuery(BaseModel):
    q: str = Field(..., description="검색할 질병명 또는 KCD 코드")
    limit: int = Field(default=5, ge=1, le=5, description="반환 개수 (최대 5)")
    offset: int = Field(default=0, ge=0, description="페이징 오프셋")


@bp.get("/diseases/search")
def search_diseases(query: DiseaseSearchQuery):
    """질병명 및 KCD 코드 검색 (SCR-03)."""
    try:
        data = disease_service.search_diseases(query.q, query.limit, query.offset)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
