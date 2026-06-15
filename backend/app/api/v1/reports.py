"""리포트 라우트 (SCR-06, F-04).

  POST /reports         리포트 생성
  GET  /reports/<id>    리포트 조회
"""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

bp = APIBlueprint("reports", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="reports")])

# TODO(이서우): report_service 연결.
