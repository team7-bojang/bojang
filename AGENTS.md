# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

> 이 저장소와 코드 주석은 한국어로 작성됩니다. 응답·주석·커밋 메시지도 한국어를 기본으로 합니다.

## 프로젝트 개요

보험 가입 정보와 질병·입원 정보를 받아 청구 가능한 보장을 탐색하고, 약관 원문 근거와 함께 분석 결과를 제공하는 서비스. 현재 대부분의 모듈이 **계약(타입·반환 구조)만 고정된 스켈레톤** 상태이며 구현은 `# TODO` 로 표시되어 있다. 새 코드를 채울 때 기존 인터페이스 계약을 깨지 않는 것이 최우선이다.

## 모노레포 구조

pnpm workspace이지만 `pnpm-workspace.yaml` 에는 `frontend` 만 포함된다. `backend` 는 별도 Python 프로젝트(`backend/.venv`)로 독립 관리한다. Husky + lint-staged 는 루트에서 동작하며 커밋 시 변경 파일에 backend(ruff) / frontend(eslint·prettier) lint 를 자동 적용한다.

```text
frontend/   React 19 + Vite + TS + Tailwind 4 + Supabase Auth (pnpm workspace)
backend/    Flask(flask-openapi3) + Pydantic + Supabase/pgvector (독립 Python)
supabase/migrations/   도메인별 SQL 마이그레이션 (도메인 소유자 단독 변경)
prompts/    LLM 프롬프트·공통 스키마 일원화 (코드에 하드코딩 금지)
tests/golden/   탐색·판정 정확도의 공식 기준 골든셋
scripts/eval_golden.py   골든셋 자동 채점 러너
```

## 자주 쓰는 명령

### Frontend (`cd frontend`)
- `pnpm dev` — 개발 서버 (http://localhost:5173)
- `pnpm build` — `tsc -b && vite build` (타입체크 포함)
- `pnpm lint` — ESLint (CI에서 `lint` + `build` 통과 필수)
- import 별칭 `@` → `frontend/src`

### Backend (`cd backend`, `.venv` 활성화 후)
- `python app/main.py` — 개발 서버 (http://localhost:5000)
- `pytest` — 전체 테스트 / `pytest tests/test_judge.py` — 단일 파일 / `pytest tests/test_judge.py::test_waiting_period_not_met_has_priority` — 단일 테스트
- `ruff check .` — lint (CI 필수) / `ruff format .` — 포맷
- 의존성: 직접 의존성은 `requirements.in` 에 추가 → `pip-compile requirements.in -o requirements.txt` 로 잠금파일 재생성. `requirements.txt` 직접 편집 금지.

### API 문서
백엔드 실행 시 자동 노출: `/openapi/swagger` · `/openapi/redoc` · `/openapi/openapi.json`. 프론트 타입은 이 `openapi.json` 을 `openapi-typescript` 입력으로 생성하는 것을 권장(`frontend/src/types/index.ts` 참고).

## 상세 규칙 (도메인별 문서)

아래 문서들이 로드 시 이 파일에 함께 포함된다:

- @docs/backend-architecture.md — 백엔드 레이어 구조, 응답 봉투, 에러, 인증, RAG/파싱, API 문서
- @docs/judge-engine.md — 룰 엔진(`judge`) 불변 규칙, 테스트·골든셋 기준
- @docs/data-model.md — 데이터 모델, 도메인 경계, 마이그레이션·스냅샷·검수 게이팅 규칙
- @CONTRIBUTING.md — Issue/브랜치/PR/커밋/리뷰/CI 개발 규칙

## 네이밍·코드 규약

- **Backend (Python)**: ruff(line-length 100, py312, double-quote). 규칙셋 `E,F,I,B,UP`. 파일/함수 `snake_case`, 클래스 `PascalCase`. 서비스 파일은 `<도메인>_service.py`, 블루프린트 변수는 `bp`.
- **Frontend (TS)**: ESLint + Prettier. `frontend/src/` 아래 `components/ features/ hooks/ pages/ store/ types/` 역할별 디렉터리. Axios 인스턴스는 `src/api/client.ts`(요청 인터셉터가 Supabase 토큰 자동 첨부).
- **타입 계약 동기화**: 프론트 도메인 타입(`frontend/src/types`)은 백엔드 Pydantic 스키마(`backend/app/schemas`)와 항상 일치해야 한다. 수기 작성보다 OpenAPI 자동 생성 권장.
- **프롬프트**: 코드에 프롬프트 문자열을 하드코딩하지 않고 `prompts/` 의 파일을 로드한다 (`parsing/` → `app/parsing/structurer.py`, `explanation/` → `app/rag/explainer.py`).
- **골든셋**: 판정·탐색 변경 시 `tests/golden/` 정탐(`expected`)과 오탐(`must_not_match`)을 함께 검증한다. 케이스 스키마는 `tests/golden/README.md` 참고.

## 브랜치 / CI

- 브랜치: `feature/*` → PR → `develop`(merge 시 자동 배포) → `main`(프로덕션).
- PR 체크(`.github/workflows/pr-check.yml`): frontend `pnpm lint && pnpm build`, backend `ruff check . && pytest` 모두 통과해야 한다.
- 배포: frontend → Vercel, backend → AWS EC2.
