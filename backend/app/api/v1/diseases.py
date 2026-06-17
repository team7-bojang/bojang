from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.core import response
from app.services import disease_service

bp = APIBlueprint("diseases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="diseases")])


class DiseaseSearchQuery(BaseModel):
    q: str = Field(default="", description="검색할 질병명 또는 KCD 코드")


@bp.get("/diseases/search")
def search_diseases(query: DiseaseSearchQuery):
    """질병명 및 KCD 코드 검색 (SCR-03)."""
    try:
        data = disease_service.search_diseases(query.q)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
