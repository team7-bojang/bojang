from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag
from pydantic import BaseModel, Field

from app.core import response
from app.schemas.common import Envelope, ErrorResponse
from app.services import disease_service

bp = APIBlueprint("diseases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="diseases")])


class DiseaseSearchQuery(BaseModel):
    q: str = Field(..., description="검색할 질병명 또는 KCD 코드")
    limit: int = Field(default=5, ge=1, le=5, description="반환 개수 (최대 5)")
    offset: int = Field(default=0, ge=0, description="페이징 오프셋")


class DiseaseItem(BaseModel):
    kcd: str
    name: str


class DiseaseSearchResult(BaseModel):
    results: list[DiseaseItem]
    total: int
    offset: int
    has_more: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "results": [
                    {"kcd": "I63", "name": "뇌경색증"},
                    {"kcd": "I63.9", "name": "상세불명의 뇌경색증"},
                ],
                "total": 2,
                "offset": 0,
                "has_more": False,
            }
        }
    }


@bp.get(
    "/diseases/search",
    responses={200: Envelope[DiseaseSearchResult], 500: ErrorResponse},
)
def search_diseases(query: DiseaseSearchQuery):
    """질병명 및 KCD 코드 검색 (SCR-03)."""
    try:
        data = disease_service.search_diseases(query.q, query.limit, query.offset)
        return response.ok(data)
    except Exception as e:
        return response.fail("server_error", str(e), 500)
