# 개발 규칙 (CONTRIBUTING)

이 저장소는 **프론트엔드 · 백엔드 · AI**를 함께 다루는 모노레포입니다.
세 영역이 동시에 개발되므로, 변경의 범위(scope)를 항상 명확히 표기하고 계약을 지키는 것을 최우선으로 합니다.

---

## 1. 작업 흐름 (Issue → Branch → PR → Merge)

1. 모든 작업은 **Issue로 task를 먼저 생성**한다. (무엇을, 왜 하는지 기록)
2. Issue 기준으로 브랜치를 따서 작업한다.
3. 작업이 끝나면 PR을 올리고 **PR에 해당 Issue를 연결**한다.
    - PR 본문에 `Closes #이슈번호` 를 넣어 머지 시 자동으로 Issue가 close 되도록 한다.
4. `develop` 으로 머지되면서 Issue가 닫힌다.

> 원칙: **Issue 없는 작업, Issue가 연결되지 않은 PR은 머지하지 않는다.**

---

## 2. 브랜치 규칙

기준 브랜치에서 분기한다. (기능 작업은 `develop` 기준)

```text
<type>/<scope>/<short-description>
```

- **type**: `feat` `fix` `chore` `refactor` `docs` `test` `style` `perf`
- **scope**: `frontend` `backend` `ai` (공통이면 `common`)
- **short-description**: 케밥케이스(kebab-case), 영문 소문자

예시:

```text
feat/frontend/login-form
fix/backend/claim-double-charge
chore/ai/prompt-loader
```

> 브랜치 이름에는 괄호 대신 슬래시(`/`)를 사용합니다. 괄호(`feat(frontend)`)는 셸 이스케이프 문제가 있어 **커밋 메시지 스코프**에서만 사용합니다. (4번 참고)

브랜치 운영:

- `main` : 배포 가능한 안정 브랜치 (직접 푸시 금지)
- `develop` : 통합 브랜치 (기능 브랜치의 머지 대상)
- 기능/수정 브랜치 : `develop` 에서 분기 → `develop` 으로 머지

---

## 3. PR 규칙

- PR을 올리면 **팀원에게 알린다.** (Slack/Discord 등 채널 공지)
- **2명 이상의 승인 없이는 `develop` 으로 머지 금지.**
- **본인 PR 셀프 머지 금지**, **본인 PR 셀프 승인 금지.**
- PR 제목은 커밋 컨벤션과 동일하게: `feat(frontend): 로그인 폼 추가`
- PR 본문에 다음을 포함한다:
    - 변경 요약 (무엇을/왜)
    - 관련 Issue (`Closes #00`)
    - 테스트 방법 / 확인 사항
    - (UI 변경 시) 스크린샷
- **CI(lint · type check · test)가 통과해야 머지 가능.** *(추가 권장)*
- PR은 **작게 쪼갠다.** 리뷰 가능한 단위로. 작업 중이면 **Draft PR**로 올린다. *(추가 권장)*

---

## 4. 커밋 메시지 규칙 (Conventional Commits)

```text
<type>(<scope>): <subject>
```

- **type**: `feat` `fix` `chore` `refactor` `docs` `test` `style` `perf`
- **scope**: `frontend` `backend` `ai` `common`
- **subject**: 한국어로 간결하게, 명령형, 마침표 없음

예시:

```text
feat(frontend): 가입 폼 유효성 검사 추가
fix(backend): claim_rule 이중차감 버그 수정
chore(ai): 프롬프트 외부 파일 로딩으로 분리
```

> 한 커밋에는 한 가지 목적만 담는다. 여러 영역을 동시에 바꿨다면 가능한 한 커밋을 분리한다.

---

## 5. 네이밍 컨벤션

> 모노레포라 **언어별 표준이 다릅니다.** 각 영역의 관례를 따르고, 영역을 섞지 않습니다.

### 프론트엔드 (TypeScript / React)

- 변수 · 함수: `camelCase`
- 컴포넌트 · 타입 · 인터페이스 · enum: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- 파일명: 컴포넌트는 `PascalCase.tsx`, 그 외 유틸/훅은 `camelCase.ts` (`useAuth.ts`)
- 불리언: `is/has/should` 접두사 (`isLoading`, `hasError`)

### 백엔드 (Python / PEP 8)

- 변수 · 함수: `snake_case`
- 클래스 · Pydantic 모델: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- 모듈 · 파일명: `snake_case.py`

### AI

- 프롬프트는 **코드에 하드코딩하지 않고** 별도 파일/템플릿으로 관리한다.
- 프롬프트 키 · 템플릿 파일명 규칙을 팀에서 통일한다. (예: `snake_case`)

### 공통

- 약어도 케이스 규칙을 따른다. (`userId` O / `userID` X, `HttpClient` O / `HTTPClient` X)
- 의미 없는 이름 금지(`data2`, `tmp`, `foo`), 줄임말 남용 금지.

---

## 6. 코드 리뷰 규칙

- 지적은 우선순위로 분류한다: **P1(머지 차단) ~ P5(사소/옵션).**
    - **P1** 머지 차단: 보안, 데이터 손상, 도메인 계약 위반, 스키마 불일치
    - **P2** 머지 전 필수: 명백한 버그, 잘못된 로직
    - **P3** 권장: 미처리 엣지케이스, 누락된 에러 처리
    - **P4** 제안: 가독성 · 구조 · 네이밍
    - **P5** 사소/옵션: 취향 수준
- **P1 · P2가 하나라도 있으면 머지하지 않는다.**
- 리뷰는 가능한 한 **빠르게**(예: 영업일 기준 24시간 내) 응답한다.
- 사소한 취향 차이로 머지를 막지 않는다.

---

## 7. 테스트 & CI *(추가 권장)*

- 신규 기능 · 버그 수정에는 **테스트를 동반**한다.
- 순수 함수(예: `judge()`)는 반드시 단위 테스트를 작성한다.
- 머지 전 lint · type check · 테스트가 모두 통과해야 한다.

---

## 8. 도메인 계약 & 마이그레이션 *(레포 고유 규칙)*

- 응답 봉투(`ok()`/`fail()`)와 `AppError` 에러 계약을 깨지 않는다.
- `judge()` 는 순수 함수로 유지하고, 판정 우선순위(`waiting_period → boundary → eligible`)를 지킨다.
- 실손 `claim_rule` 이중차감 금지 규칙을 위반하지 않는다.
- 프론트 타입(`frontend/src/types`)과 백엔드 Pydantic 스키마 계약을 일치시킨다.
- **마이그레이션은 기존 파일을 수정하지 않고 신규 파일로 추가**한다.
- 자세한 계약은 루트 `CLAUDE.md` 와 `docs/` 를 기준으로 한다.

---

## 9. 기타

- **시크릿 · 환경변수 하드코딩 금지.** `.env` 는 커밋하지 않고 `.env.example` 로 키 목록만 공유한다.
- 의존성을 추가하면 **lock 파일을 함께 커밋**하고, PR 본문에 추가 사유를 적는다.
- 동작/계약이 바뀌면 **`CLAUDE.md` · `docs/` 문서도 같은 PR에서 갱신**한다.
- 머지 전략은 팀에서 통일한다. (히스토리 정리를 위해 **Squash Merge 권장**)
- 머지 충돌은 작업 브랜치를 `develop` 최신으로 맞춘 뒤 해결한다. (rebase/merge 정책 합의)
