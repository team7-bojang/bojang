# 챗봇 `next_question` 기반 렌더러 설계

> 작성일: 2026-06-23 · 브랜치: `feature/api-policies-cases`
> 범위: **프론트엔드** (`next_question` 계약은 백엔드가 병행 제공하는 것을 전제)

## 1. 배경 / 문제

대화를 시작하면 `POST /api/v1/cases`가 호출되고, 이후 추가 정보 수집은
`POST /api/v1/cases/{caseId}/answers`로 이어진다. 모든 응답에는 최상위
`next_question` 객체가 실려 오며, 이 객체 하나가 챗봇 하단 UI를 구동한다.

대표 사례: 질병명 매칭 신뢰도가 낮을 때(`disease_match_confidence ==
"need_user_confirmation"`) 백엔드는 질병 후보(최대 5개)를 `select_button`
형태의 `next_question`으로 내려주고, 사용자는 칩으로 하나를 고른다.

### 현재 상태와의 불일치 (중요)

- 현재 백엔드 응답에는 `next_question`이 **없다**(grep 확인). `disease_kcd_candidates`,
  `questions`, `recommended_input_method` 등 옛 형태만 존재한다.
- 백엔드는 `next_question` 계약을 제공하도록 **병행 작업**한다. 본 설계의
  프론트엔드는 이 목표 계약을 기준으로 구현한다.
- 후보 페이지네이션("다음 5개")은 백엔드에 없고, 이번 범위에서도 다루지 않는다.
  옵션은 백엔드가 주는 그대로(≤5개) 노출한다.

## 2. 데이터 계약 (`next_question`)

```ts
export type QuestionInputType =
  | 'radio_button'      // 단일 선택 (칩)
  | 'checkbox_button'   // 다중 선택 (칩 + 확인)
  | 'select_button'     // 단일 선택 (칩)
  | 'text_input';       // 자유 텍스트

export interface NextQuestionOption {
  value: string;  // 백엔드로 다시 보낼 값
  label: string;  // 화면 표기
}

export interface NextQuestion {
  question_id: string;        // /answers 의 question_id 로 매핑
  question_text: string;      // 봇 말풍선 내용
  input_type: QuestionInputType;
  placeholder?: string;       // text_input 안내 텍스트
  options?: NextQuestionOption[]; // 선택형일 때 선택지
}
```

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
- `answer(value, label)` → 유저 메시지(`label`) push →
  `POST /answers { answers: [{ question_id: pendingQuestion.question_id, value }] }`
  → 다음 `pendingQuestion = res.next_question` 세팅. null이면 `done = true`.
  - 다중 선택(checkbox)일 때 `value`는 배열, `label`은 합친 문자열.
- 종료(`done`)되면 부모에 콜백으로 알린다(검수 폼 트리거는 별도 작업/플레이스홀더).

### 3.2 `QuestionPrompt` (렌더)

위치: `frontend/src/features/case/components/QuestionPrompt.tsx`

`input_type` 분기:
- `select_button` | `radio_button` → **단일 선택 칩**. 클릭 즉시 `answer(value, label)`.
  질병 후보 5개가 이 형태로 온다.
- `checkbox_button` → 다중 선택 칩 + "확인" 버튼. 확인 시 선택값 배열로 `answer`.
- `text_input` → 하단 입력창을 사용(placeholder 노출). 전송 시 `answer(text, text)`.

칩 스타일은 기존 디자인 토큰(`bg-canvas`, `bg-primary`, `ring-line`,
`rounded-2xl` 등) 및 `framer-motion` 등장 애니메이션을 재사용한다.

## 4. "해당 병명 없음 → 직접 입력" 흐름

- 백엔드가 질병 `select_button` 옵션에 "해당 병명 없음"을 포함한다.
- 사용자가 그 옵션을 고르면 프론트는 그 `value`를 평소처럼 전송한다.
- 백엔드가 **다음 응답으로 `input_type=text_input` next_question**을 내려준다.
- 프론트는 특수 분기 없이 범용 `text_input` 렌더로 자유 입력을 받는다.

→ 프론트엔드에 sentinel/로컬 전환 로직이 없다(백엔드 주도).

## 5. 종료 / 검수 폼

- `next_question === null` → 대화 완료. `useChatFlow`가 `done`을 true로 설정하고
  수집된 정보를 부모로 전달한다.
- 최종 검수 폼(Verification Form) 자체는 **이번 범위 밖**이며, 종료 콜백 +
  플레이스홀더 메시지까지만 구현한다.

## 6. 에러 / 엣지 케이스

- 네트워크/봉투 실패: 기존 `unwrap` 예외를 잡아 `error` 상태로 표기(기존 패턴 유지).
- `next_question.options`가 비어 있는 선택형: 방어적으로 입력창 안내로 폴백하거나
  에러 메시지 노출(구현 시 단순 가드).
- 응답에 `next_question` 키 자체가 없는 (구) 백엔드: `undefined`를 `null`과 동일하게
  취급(대화 종료로 간주). 백엔드 병행 작업 완료 전 임시 안전장치.

## 7. 테스트

- `useChatFlow` 단위 테스트: start→answer 시 올바른 페이로드(`question_id`,`value`)
  전송, `next_question` 전이, null일 때 `done` 처리, 다중 선택 직렬화.
- `QuestionPrompt` 렌더 테스트: 각 `input_type`별 렌더 + 선택 시 콜백 인자 검증.

## 8. 영향 파일

- 수정: `frontend/src/features/case/model.ts`(타입 추가),
  `frontend/src/features/home/components/Chatbot.tsx`(훅/프롬프트 연결,
  기존 `toBotMessages` 정리)
- 신규: `frontend/src/features/case/useChatFlow.ts`,
  `frontend/src/features/case/components/QuestionPrompt.tsx`
- `saveCaseAnswers`/`endpoints.cases.answers`는 기존 것 재사용(추가 변경 없음).

## 9. 미해결 / 백엔드 의존

- 백엔드의 `next_question` 응답 추가(질병 select_button, "해당 병명 없음" 옵션,
  후속 text_input 포함)가 본 프론트 구현의 전제다.
- 검수 폼 상세 설계는 후속 작업.
