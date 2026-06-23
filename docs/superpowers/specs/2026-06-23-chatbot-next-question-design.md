# 챗봇 `next_question` 기반 렌더러 설계

> 작성일: 2026-06-23 · 브랜치: `feature/api-policies-cases`
> 범위: **프론트엔드** (`next_question` 계약은 백엔드가 병행 제공하는 것을 전제)

## 1. 배경 / 문제

대화를 시작하면 `POST /api/v1/cases`가 호출되고, 이후 추가 정보 수집은
`POST /api/v1/cases/{caseId}/answers`로 이어진다. 모든 응답에는 최상위
`next_question` 객체가 실려 오며, 이 객체 하나가 챗봇 하단 UI를 구동한다.

대표 사례: 질병명 매칭 신뢰도가 낮을 때(`disease_match_confidence ==
"need_user_confirmation"`) 백엔드는 질병 후보 전체를 `select_button`
형태의 `next_question`으로 내려주고, 프론트가 5개씩 칩으로 노출해 하나를 고르게 한다.

### 백엔드 실제 계약 (origin/develop `8a56ad2` 기준)

`backend/app/services/case_service.py::get_next_question(case)`가 케이스 저장
상태를 순서대로 검사해 다음 질문 1개를 반환한다(없으면 `None`). `create_case`와
`save_answers` 응답 모두에 `next_question`이 실린다.

질문 순서와 실제 `input_type`:

| 순서 | question_id | input_type | options |
|---|---|---|---|
| 1 | `disease_kcd` | `select_button` | 후보 전체 (프론트가 5개씩 페이지네이션) |
| 2 | `admission_days_diagnosed` (CASE2) | `text_input` | — |
| 3 | `admission_days_current` | `text_input` | — |
| 4 | `surgery` | `radio_button` | 예/아니요 (value=boolean) |
| 5 | `treatment_items` | `checkbox_button` | 5개 (다중 선택) |
| 6 | `annual_visit_count` | `text_input` | — |
| 7 | `policy_elapsed_days` | `radio_button` | 구간 5개 (단일 선택) |
| — | (모두 충족) | — | `null` → 대화 종료 |

> **중요 1 — radio/select 렌더 구분:** 둘 다 "단일 선택"이지만 프론트 렌더가
> 다르다. `radio_button`은 옵션 전부를 단순 칩으로 노출(예/아니요, 가입기간 구간).
> `select_button`(질병 후보)은 **5개씩 페이지네이션**하고 "해당 병명 없음" 칩으로
> 다음 5개로 넘어가며, 후보 소진 시 직접 입력으로 전환한다(4절).
>
> **중요 2 — options 형태가 두 종류:** 질병(`disease_kcd`)의 options는
> `disease_kcd_candidates` 그대로라 **`{ kcd, name }`** 형태이고, 나머지는
> **`{ value, label }`** 형태다. 또 `surgery`의 `value`는 **boolean(true/false)**.
> 프론트가 정규화한다(2절).

- **후보 페이지네이션은 프론트 주도**다. 백엔드는 `select_button` options에 잘린
  5개가 아니라 **전체 후보를 보내야** 한다(현재 [case_service.py:292](backend/app/services/case_service.py#L292)
  `[:5]` 제거/완화 필요 — 백엔드 병행 작업). 프론트는 받은 전체에서 5개씩 잘라 노출한다.

## 2. 데이터 계약 (`next_question`)

```ts
export type QuestionInputType =
  | 'radio_button'      // 단일 선택 칩 (예/아니요, 가입기간 구간 등)
  | 'select_button'     // 단일 선택 칩 (질병 후보) — 5개씩 페이지네이션 + 직접입력
  | 'checkbox_button'   // 다중 선택 (칩 + 확인)
  | 'text_input';       // 자유 텍스트

// 백엔드가 보내는 raw 옵션은 두 형태 중 하나:
//   질병:   { kcd: string; name: string }
//   그 외:  { value: string | boolean; label: string }
export type RawQuestionOption =
  | { kcd: string; name: string }
  | { value: string | boolean; label: string };

export interface NextQuestion {
  question_id: string;        // /answers 의 question_id 로 매핑
  question_text: string;      // 봇 말풍선 내용
  input_type: QuestionInputType;
  placeholder?: string;       // text_input 안내 텍스트
  options?: RawQuestionOption[]; // 선택형일 때 선택지 (raw)
}

// 프론트 내부 정규화 형태 (렌더·전송에 사용)
export interface NormalizedOption {
  value: string | boolean; // /answers value 로 그대로 전송
  label: string;           // 화면 표기
}
```

정규화 규칙(`{kcd,name}` → `{value: kcd, label: name}`, `{value,label}`은 그대로).
`value`의 boolean(surgery)은 변환 없이 그대로 `/answers`로 전송한다.

응답 타입 확장(`frontend/src/features/case/model.ts`):
- `CreateCaseResponse`에 `next_question?: NextQuestion | null` 추가
- `SaveAnswersResponse`에 `next_question?: NextQuestion | null` 추가

> 타입 계약 동기화 원칙(CLAUDE.md)에 따라, 백엔드 Pydantic 스키마가 확정되면
> OpenAPI 자동 생성 타입과 일치시킨다. 그 전까지는 본 수기 타입을 단일 출처로 둔다.

## 3. 컴포넌트 구조 (접근법 A)

```
Chatbot.tsx                     (얇은 컨테이너 — 입력/스크롤/잠금 UI)
  └─ useChatFlow()              (흐름 로직 격리 · 테스트 대상)
  └─ <QuestionPrompt />         (input_type 분기 렌더 · 순수 프레젠테이션)
```

### 3.1 `useChatFlow` (흐름 로직)

위치: `frontend/src/features/case/useChatFlow.ts`

상태:
- `messages: ChatMessage[]`
- `caseId: string | null`
- `pendingQuestion: NextQuestion | null`
- `submitting: boolean`, `error: string | null`
- `done: boolean` (대화 종료 여부)

동작:
- `start(situation)` → `POST /cases` → 봇 메시지(`question_text`) push +
  `pendingQuestion = res.next_question`. `next_question`이 null이면 즉시 `done`.
- `answer(questionId, value, label)` → 유저 메시지(`label`) push →
  `POST /answers { answers: [{ question_id: questionId, value }] }`
  → 다음 `pendingQuestion = res.next_question` 세팅. null이면 `done = true`.
  - `questionId`는 보통 `pendingQuestion.question_id`지만, 질병 직접 입력 시엔
    `'disease_name'`을 넘긴다(4절). `QuestionPrompt`가 결정해 전달한다.
  - 다중 선택(checkbox)일 때 `value`는 배열, `label`은 합친 문자열.
- 종료(`done`)되면 부모에 콜백으로 알린다(검수 폼 트리거는 별도 작업/플레이스홀더).

### 3.2 `QuestionPrompt` (렌더)

위치: `frontend/src/features/case/components/QuestionPrompt.tsx`

`input_type` 분기 (옵션은 먼저 `NormalizedOption[]`로 정규화):
- `radio_button` → **단순 단일 선택 칩**. 옵션 전부 노출. 클릭 즉시
  `answer(question_id, value, label)`. 예/아니요(surgery), 가입기간 구간(policy).
- `select_button` → **페이지네이션 단일 선택 칩**(질병 후보). 한 번에 5개 노출 +
  "해당 병명 없음" 칩. 자세한 동작은 4절. 후보 클릭 시 `answer('disease_kcd', kcd, name)`.
- `checkbox_button` → 다중 선택 칩 + "확인" 버튼. 확인 시 선택값 배열로 `answer`.
- `text_input` → 하단 입력창을 사용(placeholder 노출). 전송 시 `answer(text, text)`.

칩 스타일은 기존 디자인 토큰(`bg-canvas`, `bg-primary`, `ring-line`,
`rounded-2xl` 등) 및 `framer-motion` 등장 애니메이션을 재사용한다.

## 4. 질병 후보 페이지네이션 + 직접 입력 (프론트 주도)

`select_button`(질병 후보) 전용 동작. 백엔드가 전체 후보를 options로 보내준다는
전제(1절) 하에, 페이지네이션·직접입력 전환은 **전적으로 프론트에서** 처리한다.

- `QuestionPrompt`(또는 전용 `DiseasePicker`)가 정규화된 옵션을 5개 단위 페이지로 나눈다.
- 현재 페이지의 후보 5개를 칩으로 + 하단에 **"해당 병명 없음"** 칩 1개를 노출.
- 후보 칩 클릭 → `answer('disease_kcd', option.value /*=kcd*/, option.label /*=name*/)`.
- "해당 병명 없음" 클릭:
  - 다음 페이지가 남아 있으면 → **다음 5개로 이동**(API 호출 없음, 로컬 상태).
  - 마지막 페이지였으면 → **직접 입력 모드**로 전환(자유 텍스트 입력창).
- 직접 입력 전송 → `answer('disease_name', text, text)`.
  (백엔드 `save_answers`는 `question_id == "disease_name"`을 자유 텍스트로 저장하고
  confidence를 high로 올린다 — [case_service.py:780](backend/app/services/case_service.py#L780).)

→ 페이지 인덱스·직접입력 모드는 `QuestionPrompt` 로컬 상태. 한 질문(`pendingQuestion`)이
바뀌면 초기화한다.

## 5. 종료 / 검수 폼

- `next_question === null` → 대화 완료. `useChatFlow`가 `done`을 true로 설정하고
  수집된 정보를 부모로 전달한다.
- 최종 검수 폼(Verification Form) 자체는 **이번 범위 밖**이며, 종료 콜백 +
  플레이스홀더 메시지까지만 구현한다.

## 6. 에러 / 엣지 케이스

- 네트워크/봉투 실패: 기존 `unwrap` 예외를 잡아 `error` 상태로 표기(기존 패턴 유지).
- `next_question.options`가 비어 있는 선택형: 방어적으로 입력창 안내로 폴백하거나
  에러 메시지 노출(구현 시 단순 가드).
- 질병 후보가 5개 이하: 페이지가 1개뿐이라 "해당 병명 없음" 클릭 시 바로 직접 입력.
- 응답에 `next_question` 키 자체가 없을 때: `undefined`를 `null`과 동일하게 취급
  (대화 종료로 간주)하는 방어 코드.

## 7. 테스트

- `useChatFlow` 단위 테스트: start→answer 시 올바른 페이로드(`question_id`,`value`)
  전송, `next_question` 전이, null일 때 `done` 처리, 다중 선택 직렬화.
- `QuestionPrompt` 렌더 테스트: 각 `input_type`별 렌더 + 선택 시 콜백 인자 검증
  (질병은 `disease_kcd`+kcd, surgery는 boolean value 등).
- 질병 페이지네이션 테스트: 후보 12개 → 5/5/2 페이징, "해당 병명 없음"이 다음
  페이지로 이동, 마지막 페이지에서 직접 입력 모드 전환 후 `disease_name`으로 전송.
- 옵션 정규화 테스트: `{kcd,name}`·`{value,label}`(boolean 포함) 모두 `NormalizedOption`으로.

## 8. 영향 파일

- 수정: `frontend/src/features/case/model.ts`(타입 추가),
  `frontend/src/features/home/components/Chatbot.tsx`(훅/프롬프트 연결,
  기존 `toBotMessages` 정리)
- 신규: `frontend/src/features/case/useChatFlow.ts`,
  `frontend/src/features/case/components/QuestionPrompt.tsx`
- `saveCaseAnswers`/`endpoints.cases.answers`는 기존 것 재사용(추가 변경 없음).

## 9. 미해결 / 백엔드 의존

- **백엔드:** 질병 `select_button` options를 잘린 5개가 아니라 **전체 후보**로 보내야
  프론트 페이지네이션이 동작한다([case_service.py:292](backend/app/services/case_service.py#L292)
  `[:5]` 제거/완화 — 병행 작업). 그 전까지는 1페이지(≤5개)만 노출되고 "해당 병명
  없음"은 곧장 직접 입력으로 간다(별도 코드 변경 없이 자동).
- 검수 폼 상세 설계는 후속 작업.
