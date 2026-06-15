# 백엔드 아키텍처

> `CLAUDE.md` 에서 `@docs/backend-architecture.md` 로 로드됨.

요청 흐름은 엄격한 레이어 분리를 따른다:

```
api/v1/<도메인>.py   라우트(APIBlueprint) — Pydantic 스키마 입출력만
   ↓
services/<도메인>_service.py   오케스트레이션 (DB·judge·rag 조합)
   ↓
judge/ · rag/ · parsing/   순수 도메인 로직
   ↓
db/ (Supabase) · llm/ (OpenAI·Claude)   외부 I/O
```

- **앱 팩토리**: `app/factory.py::create_app()` 가 `OpenAPI`(Flask 서브클래스) 앱을 만들고 CORS·라우트를 구성. 진입점은 `app/main.py`.
- **라우트 등록**: 도메인별 `APIBlueprint`(모두 `url_prefix="/api/v1"`)를 `app/api/v1/__init__.py::register_v1` 에 등록. 새 도메인은 `_DOMAIN_BLUEPRINTS` 에 추가. `health` 만 버전 무관.
- **응답 봉투** (불변 계약): 모든 응답은 `app/core/response.py` 의 `ok()`/`fail()` 만 사용 → `{success, data|error, timestamp, request_id}`. Swagger 표시용 모델은 `app/schemas/common.py::Envelope[T]`.
- **에러 처리**: 도메인 예외는 `app/core/errors.py::AppError` 하위(`http_status`·`code` 보유)를 던진다. HTTP 상태/에러코드는 여기 정의된 매핑을 따른다.
- **설정**: `app/config.py::settings` (pydantic-settings, `.env` 로드). 환경변수 키는 `.env.example` 참고.
- **인증**: `Authorization: Bearer <jwt>` → `app/auth/middleware.py::require_auth` 가 검증 후 `g.user_id` 주입. 본인 데이터 접근(`/cases/my` 등)은 이 `user_id` 기준으로 필터.

## API 문서

백엔드 실행 시 자동 노출: `/openapi/swagger` · `/openapi/redoc` · `/openapi/openapi.json`. 프론트 타입은 이 `openapi.json` 을 `openapi-typescript` 입력으로 생성하는 것을 권장(`frontend/src/types/index.ts` 참고).

## RAG / 파싱

- `rag/`: `chunker → embedder → retriever → explainer → citation`. 검색은 메타데이터 필터(보험ID+trigger_type) + 벡터 유사도 + 키워드 가산점.
- `parsing/`: 약관 PDF → `extractor → sectioner → structurer`.
- 설명 생성은 **원문 컨텍스트 한정**(LLM 환각 방지). 인용은 `raw_text` 로 검증.
