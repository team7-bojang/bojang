"""상황 입력·이력 라우트 (SCR-03·07).

  POST /cases          상황 입력 저장
  POST /cases/parse    (선택, F-07) 자연어 → 폼 자동완성
  GET  /cases/my       내 분석 이력 목록
"""

from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

bp = APIBlueprint("cases", __name__, url_prefix="/api/v1", abp_tags=[Tag(name="cases")])

# TODO(조윤/이서우): case_service 연결. /cases/my 는 미들웨어 user_id 기준 본인 것만.
