"""보험 등록·조회 라우트 (F-01 노출, SCR-01·02).

엔드포인트:
  GET  /policies/presets        선탑재 상품 목록
  POST /policies/select         선탑재 상품 등록
  POST /policies/upload         약관 PDF 업로드·분석
  GET  /policies/my             내 보험·특약 목록 (riders: claim_rule·source_pages 포함)
  GET  /policies/<id>/source    약관 원문 조회 (?page=)
"""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

bp = APIBlueprint("policies", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="policies")])

# TODO(진미경/조윤): policy_service 연결. 1주차에는 mocks/policies 응답으로 우선 연결.
#   @bp.get("/policies/presets", responses={200: ...}) 형태로 스키마 지정 시 자동 문서화.
