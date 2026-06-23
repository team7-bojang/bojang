# Backend (보장 분석 API)

> Flask(flask-openapi3) + Pydantic + Supabase/pgvector 기반 백엔드.
> 이 문서는 **백엔드 단독 개발자용 실전 가이드**다. 레이어 구조·도메인 계약 등 상세 규칙은
> 루트 [`CLAUDE.md`](../CLAUDE.md) 와 [`docs/`](../docs) 가 단일 출처(SSOT)이며, 여기서는 링크로 연결한다.

---

## 1. 빠른 시작

```bash
cd backend
python -m venv .venv            # 최초 1회
source .venv/Scripts/activate   # Windows Git Bash / PowerShell은 .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py              # http://localhost:5000
```

`backend` 는 pnpm workspace 와 분리된 **독립 Python 프로젝트**다 (`backend/.venv`). 루트 monorepo 명령과 섞지 않는다.

### 환경 변수

`.env` 키 목록은 루트 `.env.example` 참고. 시크릿은 커밋 금지.
`SUPABASE_URL`/`SUPABASE_KEY` 가 없으면 자동으로 **Mock DB**(`app/db/mock_db.py`)로 폴백한다.

---

## 2. 디렉터리 구조

요청은 엄격한 레이어 분리를 따른다 (상세: [`docs/backend-architecture.md`](../docs/backend-architecture.md)).

```
app/
  main.py            진입점 (create_app 실행)
  factory.py         앱 팩토리 (OpenAPI 앱 생성, CORS·라우트 등록)
  config.py          설정 (pydantic-settings, .env 로드)
  api/v1/<도메인>.py  라우트(APIBlueprint) — Pydantic 입출력만
  services/          오케스트레이션 (DB·judge·rag 조합)
  judge/             순수 판정 로직 (DB·LLM 접근 없음)
  rag/               chunker → embedder → retriever → explainer → citation
  parsing/           약관 PDF → extractor → sectioner → structurer
  schemas/           Pydantic 입출력 모델 (프론트 타입과 계약 일치)
  core/              response(응답 봉투) · errors · constants
  auth/              JWT 인증 미들웨어 (require_auth → g.user_id)
  db/                Supabase 클라이언트 / Mock DB
  llm/               OpenAI·Claude 클라이언트
tests/               pytest (judge 계약 테스트 등)
```

---

## 3. 자주 쓰는 명령

| 목적 | 명령 | 비고 |
|---|---|---|
| 개발 서버 | `python app/main.py` | http://localhost:5000 |
| 전체 테스트 | `pytest` | `testpaths=tests`, `pythonpath=.` |
| 단일 파일 | `pytest tests/test_judge.py` | |
| 단일 테스트 | `pytest tests/test_judge.py::test_...` | |
| 린트 | `ruff check .` | **CI 필수** |
| 린트 자동수정 | `ruff check . --fix` | 안전한 수정만. `--unsafe-fixes` 는 검토 후 |
| 포맷 | `ruff format .` | 코드 스타일 정렬 |

### API 문서 (서버 실행 시 자동 노출)

- `/openapi/swagger`
- 프론트 타입은 이 `openapi.json` 을 `openapi-typescript` 로 생성하는 것을 권장.

### 의존성 추가

직접 의존성은 `requirements.in` 에 추가 → `pip-compile requirements.in -o requirements.txt` 로 잠금파일 재생성.
**`requirements.txt` 직접 편집 금지.** lock 파일은 PR에 함께 커밋한다.

---

## 4. 코드 규칙

### ruff 설정 (`pyproject.toml` 기준 — 실제값)

- `line-length = 120`, `target-version = "py312"`
- lint select: `E, F, I, B, UP` / ignore: `E501`(줄 길이는 formatter가 관리)
- format: `quote-style = "double"`, `indent-style = "space"`, `line-ending = "lf"`

### 네이밍

- 파일·함수·변수: `snake_case` / 클래스·Pydantic 모델: `PascalCase` / 상수: `UPPER_SNAKE_CASE`
- 서비스 파일은 `<도메인>_service.py`, 블루프린트 변수는 `bp`

### 깨면 안 되는 도메인 계약

- 모든 응답은 `app/core/response.py` 의 `ok()`/`fail()` 만 사용 → `{success, data|error, timestamp, request_id}`
- 도메인 예외는 `app/core/errors.py::AppError` 하위를 던진다
- `judge(case, rider)` 는 **순수 함수**. 판정 우선순위 `waiting_period → boundary → eligible`, 실손 `claim_rule` 이중차감 금지 (상세: [`docs/judge-engine.md`](../docs/judge-engine.md))
- 프론트 타입(`frontend/src/types`)과 `app/schemas` 계약 일치

---

## 5. 개발 환경 함정 (자주 겪는 혼란)

이 절은 실제로 반복해서 부딪힌 문제들을 모았다. **에디터 경고 ≠ 빌드 에러** 임을 먼저 이해할 것.

### 5.1 ruff 는 반드시 `backend/` 에서 돌린다

ruff 설정(`line-length 120` 등)은 `backend/pyproject.toml` 에만 있다.
**루트나 `scripts/` 에서 ruff 를 돌리면 이 설정이 적용되지 않고 ruff 기본값(line-length 88)으로 동작**해, backend 와 다른 기준으로 포맷·린트된다.

```bash
# OK — backend 설정 적용
cd backend && ruff check . && ruff format .

# 주의 — scripts/* 는 backend 설정 밖. CI 도 backend 에서만 ruff 를 돌린다.
```

> `scripts/` 파일은 backend 설정의 적용 대상이 아니다. 같은 기준으로 포맷하고 싶다면 backend 에 복사하지 말고, scripts 도 `cd backend` 기준 경로로 묶거나 별도 설정을 두는 방안을 팀과 합의한다. (현재는 CI 비대상)

### 5.2 `ruff check` 와 `ruff format` 은 다르다

- `ruff check` = **린트** (버그성 패턴·미사용 변수·import 정렬 규칙 위반 탐지). diff 작다.
- `ruff format` = **포매터** (따옴표·줄바꿈·들여쓰기 스타일 정렬). 파일 전반에 걸쳐 diff 가 크게 난다.

큰 포맷 diff 가 보이면 대개 `ruff format` 을 돌린 결과다. 린트 수정과 헷갈리지 말 것.

### 5.3 Pylance 경고는 "에러"가 아니라 "조언"이다

Pylance(= Pyright 엔진 기반 VS Code 언어 서버)는 **코드를 실행하지 않고 정적 분석**한다.
빨간 밑줄이 떠도 `ruff check` 와 `pytest` 가 통과하면 기능상 문제는 없다. 다만 가끔 진짜 버그가 섞여 있으니 **새로 짠 코드의 경고는 한 번씩 확인**한다.

경고 해소 우선순위:

1. **원인을 코드로 고친다** (예: `None` 가능성 → 가드/인자로 받기). 코드가 실제로 안전해진다.
2. **정말 타입으로 표현 불가능한 검증된 예외만** `# type: ignore[...]` 로 억제하고 **반드시 이유 주석**을 단다.
3. 무지성 `# type: ignore` 남발 금지 — 진짜 버그 경고까지 묻힌다.

자주 본 경고:

- `Import "app.xxx" could not be resolved` — `scripts/*` 가 런타임에 `sys.path` 로 backend 를 추가하지만 정적 분석기는 모른다. → 루트 `.vscode/settings.json` 의 `python.analysis.extraPaths: ["backend"]` 로 해결됨. (실행 동작과 무관)
- `"get" is not a known attribute of "None"` (`reportOptionalMemberAccess`) — `request.view_args` 등 `X | None` 타입에 `.get()` 호출. 라우트 핸들러 안에선 실제로 None 이 아니지만, 가드(`(request.view_args or {}).get(...)`) 또는 경로 파라미터를 함수 인자로 받으면 깔끔히 해소된다.

### 5.4 Pylance ≠ Pydantic

- **Pylance**: 에디터 도구. 작성 시점(정적)에 **코드**의 타입을 검사. 끄면 경고만 사라지고 실행은 멀쩡.
- **Pydantic**: 런타임 라이브러리. 실행 시점에 **실제 데이터**를 스키마로 검증/변환. 동작의 핵심.

둘은 같은 타입 주석을 공유하지만(작성 때 Pylance, 실행 때 Pydantic) 역할이 다르다.

---

## 6. 커밋 훅 / 브랜치 / CI

### 커밋 시 ruff 자동 실행 (pre-commit 훅)

`git commit` 하면 Husky 가 lint-staged 를 실행해 ruff 가 자동으로 한 번 돈다.

```
git commit
  └─ .husky/pre-commit  →  pnpm exec lint-staged
       └─ backend/.lintstagedrc.json  →  "*.py": ["ruff check --fix", "ruff format"]
```

알아둘 점:

- **스테이징된 파일만** 검사한다 (`git add` 된 것만). 전체 점검은 `ruff check .` 를 따로 돌린다.
- `--fix` 라 자동 수정 후 재스테이징한다. 단 **자동 수정 불가한 규칙**(예: `B904` `raise ... from`)이 걸리면 ruff 가 실패해 **커밋이 중단**된다 (게이트 역할).
- ⚠️ **`scripts/*.py` 는 이 훅을 타지 않는다.** `.lintstagedrc.json` 이 `backend/` 에만 있고 `scripts/` 는 그 밖이라 매칭되는 설정이 없다. CI 도 backend 에서만 ruff 를 돌리므로, `scripts/` 는 커밋 훅·CI 어디에서도 검사되지 않는다 → 직접 `ruff check` 로 확인 (5.1 참고).

### 브랜치 / CI

- 브랜치: `<type>/<scope>/<desc>` (예: `feat/backend/claim-rule`) → PR → `develop`
- PR 체크: backend 는 `ruff check . && pytest` 통과 필수
- 상세 규칙: [`CONTRIBUTING.md`](../CONTRIBUTING.md)
