"""질병 검색 라우트 (SCR-03).

  GET /diseases/search?q=   질병명 → KCD 매핑 검색
"""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

bp = APIBlueprint("diseases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="diseases")])

# TODO(이서우): disease_service(KCD 매핑) 연결.
