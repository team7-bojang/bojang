# 챗봇 `next_question` 렌더러 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모든 케이스 API 응답에 실리는 `next_question` 객체로 챗봇 하단 UI(칩·체크박스·입력창)를 구동하고, 질병 후보는 5개씩 페이지네이션 + 직접입력으로 처리한다.

**Architecture:** 흐름 로직은 `useChatFlow` 훅에 격리(순수 호출/상태)하고, 렌더는 `QuestionPrompt`가 `input_type`별로 분기한다(질병 전용 `DiseasePicker` 분리). `Chatbot.tsx`는 훅+프롬프트를 연결하는 얇은 컨테이너가 된다.

**Tech Stack:** React 19 + TypeScript + Vite, Tailwind 4, framer-motion, axios. 테스트는 신규 도입하는 **vitest + @testing-library/react + jsdom**.

**Spec:** `docs/superpowers/specs/2026-06-23-chatbot-next-question-design.md`

---

## 파일 구조

| 파일 | 역할 | 작업 |
|---|---|---|
| `frontend/vitest.config.ts` | 테스트 러너 설정(jsdom·alias·setup) | Create (Task 1) |
| `frontend/src/test/setup.ts` | jest-dom 매처 로드 | Create (Task 1) |
| `frontend/package.json` | devDeps + `test` 스크립트 | Modify (Task 1) |
| `frontend/tsconfig.app.json` | 테스트 글로벌 타입 추가 | Modify (Task 1) |
| `frontend/src/features/case/model.ts` | `next_question` 타입 계약 | Modify (Task 2) |
| `frontend/src/features/case/options.ts` | 옵션 정규화 순수 함수 | Create (Task 3) |
| `frontend/src/features/case/queries.ts` | `answerCase` 래퍼 | Modify (Task 4) |
| `frontend/src/features/case/useChatFlow.ts` | 대화 흐름 훅 | Create (Task 4) |
| `frontend/src/features/case/components/Chip.tsx` | 공용 칩 버튼 | Create (Task 5) |
| `frontend/src/features/case/components/QuestionPrompt.tsx` | `input_type` 분기 렌더 | Create (Task 5) |
| `frontend/src/features/case/components/DiseasePicker.tsx` | 질병 페이지네이션+직접입력 | Create (Task 6) |
| `frontend/src/features/home/components/Chatbot.tsx` | 훅·프롬프트 연결 | Modify (Task 7) |

> 모든 명령은 `frontend/`에서 실행한다. import 별칭 `@` → `frontend/src`.

---

## Task 1: 테스트 인프라(vitest + testing-library) 셋업

**Files:**
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/sanity.test.ts` (검증용, Step 5에서 삭제)
- Modify: `frontend/package.json`
- Modify: `frontend/tsconfig.app.json`

- [ ] **Step 1: 개발 의존성 설치**

Run:
```bash
cd frontend && pnpm add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```
Expected: `package.json` devDependencies에 5개 패키지 추가, `pnpm-lock.yaml` 갱신.

- [ ] **Step 2: vitest 설정 파일 생성**

`frontend/vitest.config.ts`:
```ts
import path from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

`frontend/src/test/setup.ts`:
```ts
import '@testing-library/jest-dom';
```

- [ ] **Step 3: package.json 스크립트 + tsconfig 타입 추가**

`frontend/package.json`의 `scripts`에 추가:
```json
    "test": "vitest run",
    "test:watch": "vitest"
```

`frontend/tsconfig.app.json`의 `compilerOptions.types`를 교체:
```json
    "types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"],
```

- [ ] **Step 4: sanity 테스트 작성 후 실행**

`frontend/src/test/sanity.test.ts`:
```ts
describe('test infra', () => {
  it('runs vitest with globals', () => {
    expect(1 + 1).toBe(2);
  });
});
```
Run: `pnpm test`
Expected: PASS (1 passed). globals(`describe/it/expect`)가 import 없이 동작하면 설정 정상.

- [ ] **Step 5: sanity 테스트 삭제 + 빌드 확인**

```bash
rm src/test/sanity.test.ts
pnpm build
```
Expected: `tsc -b && vite build` 성공(테스트 글로벌 타입이 build를 깨지 않음).

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml frontend/vitest.config.ts frontend/src/test/setup.ts frontend/tsconfig.app.json
git commit -m "test(frontend): vitest + testing-library 테스트 인프라 도입"
```

---

## Task 2: `next_question` 타입 계약 추가

**Files:**
- Modify: `frontend/src/features/case/model.ts`

타입 전용 작업이라 빌드(`tsc`)로 검증한다.

- [ ] **Step 1: model.ts에 타입 추가**

`frontend/src/features/case/model.ts` 상단 `DiseaseCandidate` 선언 아래에 추가:
```ts
export type QuestionInputType =
  | 'radio_button'
  | 'select_button'
  | 'checkbox_button'
  | 'text_input';

// 백엔드 raw 옵션: 질병은 {kcd,name}, 그 외는 {value,label}(value는 boolean 가능)
export type RawQuestionOption =
  | { kcd: string; name: string }
  | { value: string | boolean; label: string };

export interface NextQuestion {
  question_id: string;
  question_text: string;
  input_type: QuestionInputType;
  placeholder?: string;
  options?: RawQuestionOption[];
}

// 프론트 내부 정규화 형태
export interface NormalizedOption {
  value: string | boolean;
  label: string;
}

// /answers 로 전송하는 값 (단일/불리언/다중)
export type AnswerValue = string | boolean | Array<string | boolean>;
```

- [ ] **Step 2: 응답 타입에 `next_question` 필드 추가**

`CreateCaseResponse` 인터페이스 끝(`message?: string | null;` 다음 줄)에 추가:
```ts
  next_question?: NextQuestion | null;
```

`SaveAnswersResponse` 인터페이스 끝(`case_id?: string;` 다음 줄)에 추가:
```ts
  next_question?: NextQuestion | null;
```

- [ ] **Step 3: 타입 체크**

Run: `pnpm build`
Expected: 성공(신규 타입이 기존 코드와 충돌 없음).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/case/model.ts
git commit -m "feat(frontend): next_question 타입 계약 추가"
```

---

## Task 3: 옵션 정규화 순수 함수 (TDD)

**Files:**
- Create: `frontend/src/features/case/options.ts`
- Test: `frontend/src/features/case/options.test.ts`

- [ ] **Step 1: 실패하는 테스트 작성**

`frontend/src/features/case/options.test.ts`:
```ts
import { normalizeOptions } from './options';

describe('normalizeOptions', () => {
  it('질병 {kcd,name} 옵션을 {value,label}로 변환한다', () => {
    const result = normalizeOptions([
      { kcd: 'G56', name: '손목터널증후군' },
      { kcd: 'S60', name: '손목 타박상' },
    ]);
    expect(result).toEqual([
      { value: 'G56', label: '손목터널증후군' },
      { value: 'S60', label: '손목 타박상' },
    ]);
  });

  it('{value,label} 옵션은 그대로 두고 boolean value를 보존한다', () => {
    const result = normalizeOptions([
      { value: true, label: '예' },
      { value: false, label: '아니요' },
    ]);
    expect(result).toEqual([
      { value: true, label: '예' },
      { value: false, label: '아니요' },
    ]);
  });

  it('options가 없으면 빈 배열을 반환한다', () => {
    expect(normalizeOptions()).toEqual([]);
    expect(normalizeOptions(undefined)).toEqual([]);
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test options`
Expected: FAIL ("normalizeOptions" not exported / module not found).

- [ ] **Step 3: 최소 구현**

`frontend/src/features/case/options.ts`:
```ts
import type { NormalizedOption, RawQuestionOption } from './model';

export function normalizeOptions(options: RawQuestionOption[] = []): NormalizedOption[] {
  return options.map(opt =>
    'kcd' in opt ? { value: opt.kcd, label: opt.name } : { value: opt.value, label: opt.label }
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test options`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/case/options.ts frontend/src/features/case/options.test.ts
git commit -m "feat(frontend): 질병/일반 옵션 정규화 함수 추가"
```

---

## Task 4: `useChatFlow` 흐름 훅 (TDD)

**Files:**
- Modify: `frontend/src/features/case/queries.ts`
- Create: `frontend/src/features/case/useChatFlow.ts`
- Test: `frontend/src/features/case/useChatFlow.test.ts`

- [ ] **Step 1: queries.ts에 `answerCase` 래퍼 추가**

`frontend/src/features/case/queries.ts` 수정. import 두 줄을 교체:
```ts
import { createCase, getCaseDashboard, patchCaseDashboard, patchExtractedInfo, saveCaseAnswers } from './api/cases';
import type { CreateCaseRequest, SaveAnswersRequest } from './model';
```
그리고 `startCaseAnalysis` 함수 아래에 추가:
```ts
export async function answerCase(caseId: string, body: SaveAnswersRequest) {
  return saveCaseAnswers(caseId, body);
}
```

- [ ] **Step 2: 실패하는 훅 테스트 작성**

`frontend/src/features/case/useChatFlow.test.ts`:
```ts
import { act, renderHook, waitFor } from '@testing-library/react';

import { useChatFlow } from './useChatFlow';
import * as queries from './queries';

vi.mock('./queries');

const mockedStart = vi.mocked(queries.startCaseAnalysis);
const mockedAnswer = vi.mocked(queries.answerCase);

const diseaseQuestion = {
  question_id: 'disease_kcd',
  question_text: '가장 가까운 질병을 골라주세요.',
  input_type: 'select_button' as const,
  options: [{ kcd: 'G56', name: '손목터널증후군' }],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useChatFlow', () => {
  it('start: /cases 응답의 next_question을 pendingQuestion으로 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);

    const { result } = renderHook(() =>
      useChatFlow({ selectedPolicyIds: ['p1'] })
    );

    await act(async () => {
      await result.current.start('계단에서 넘어져 손목을 다쳤어요');
    });

    expect(mockedStart).toHaveBeenCalledWith({
      service_type: 'CASE1',
      policy_ids: ['p1'],
      initial_situation: '계단에서 넘어져 손목을 다쳤어요',
    });
    expect(result.current.caseId).toBe('c1');
    expect(result.current.pendingQuestion).toEqual(diseaseQuestion);
    expect(result.current.messages.at(-1)).toEqual({
      role: 'bot',
      text: '가장 가까운 질병을 골라주세요.',
    });
  });

  it('answer: question_id/value를 전송하고 다음 next_question으로 전이한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    const surgeryQuestion = {
      question_id: 'surgery',
      question_text: '수술도 받으셨나요?',
      input_type: 'radio_button' as const,
      options: [{ value: true, label: '예' }],
    };
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: surgeryQuestion } as never);

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });

    expect(mockedAnswer).toHaveBeenCalledWith('c1', {
      answers: [{ question_id: 'disease_kcd', value: 'G56' }],
    });
    expect(result.current.pendingQuestion).toEqual(surgeryQuestion);
  });

  it('next_question이 null이면 done=true가 되고 onDone을 호출한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: null } as never);
    const onDone = vi.fn();

    const { result } = renderHook(() =>
      useChatFlow({ selectedPolicyIds: ['p1'], onDone })
    );
    await act(async () => {
      await result.current.start('손목');
    });

    await waitFor(() => expect(result.current.done).toBe(true));
    expect(result.current.pendingQuestion).toBeNull();
    expect(onDone).toHaveBeenCalledWith('c1');
  });

  it('start 실패(case_id 없음) 시 error를 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: null, message: '실패' } as never);

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));
    await act(async () => {
      await result.current.start('손목');
    });

    expect(result.current.error).toBe('실패');
    expect(result.current.caseId).toBeNull();
  });
});
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `pnpm test useChatFlow`
Expected: FAIL (useChatFlow 모듈 없음).

- [ ] **Step 4: 훅 구현**

`frontend/src/features/case/useChatFlow.ts`:
```ts
import { useCallback, useState } from 'react';

import type { AnswerValue, NextQuestion } from './model';
import { answerCase, startCaseAnalysis } from './queries';

export interface ChatMessage {
  role: 'bot' | 'user';
  text: string;
}

interface ApplyTarget {
  next_question?: NextQuestion | null;
  message?: string | null;
}

interface UseChatFlowParams {
  selectedPolicyIds: string[];
  onCaseCreated?: (caseId: string, selectedPolicyIds: string[]) => void;
  onDone?: (caseId: string) => void;
}

const DONE_MESSAGE = '필요한 정보를 모두 확인했어요. 분석을 준비할게요.';

export function useChatFlow({ selectedPolicyIds, onCaseCreated, onDone }: UseChatFlowParams) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const pushMessage = (role: ChatMessage['role'], text: string) =>
    setMessages(prev => [...prev, { role, text }]);

  const applyResponse = useCallback(
    (res: ApplyTarget, resolvedCaseId: string) => {
      const next = res.next_question ?? null;
      if (next) {
        pushMessage('bot', next.question_text);
        setPendingQuestion(next);
        return;
      }
      pushMessage('bot', res.message ?? DONE_MESSAGE);
      setPendingQuestion(null);
      setDone(true);
      onDone?.(resolvedCaseId);
    },
    [onDone]
  );

  const start = useCallback(
    async (situation: string) => {
      const value = situation.trim();
      if (!value || caseId || submitting) {
        return;
      }
      pushMessage('user', value);
      setError(null);
      setSubmitting(true);
      try {
        const res = await startCaseAnalysis({
          service_type: 'CASE1',
          policy_ids: selectedPolicyIds,
          initial_situation: value,
        });
        if (!res.case_id) {
          setError(res.message ?? '분석 가능한 케이스를 만들지 못했습니다.');
          return;
        }
        setCaseId(res.case_id);
        onCaseCreated?.(res.case_id, selectedPolicyIds);
        applyResponse(res, res.case_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : '분석 세션을 시작하지 못했습니다.');
      } finally {
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, onCaseCreated, selectedPolicyIds, submitting]
  );

  const answer = useCallback(
    async (questionId: string, value: AnswerValue, label: string) => {
      if (!caseId || submitting) {
        return;
      }
      pushMessage('user', label);
      setError(null);
      setSubmitting(true);
      try {
        const res = await answerCase(caseId, { answers: [{ question_id: questionId, value }] });
        applyResponse(res, caseId);
      } catch (err) {
        setError(err instanceof Error ? err.message : '답변을 저장하지 못했습니다.');
      } finally {
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, submitting]
  );

  return { messages, caseId, pendingQuestion, submitting, error, done, start, answer };
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `pnpm test useChatFlow`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/case/queries.ts frontend/src/features/case/useChatFlow.ts frontend/src/features/case/useChatFlow.test.ts
git commit -m "feat(frontend): next_question 기반 대화 흐름 useChatFlow 훅 추가"
```

---

## Task 5: `Chip` + `QuestionPrompt` 렌더러 (TDD)

**Files:**
- Create: `frontend/src/features/case/components/Chip.tsx`
- Create: `frontend/src/features/case/components/QuestionPrompt.tsx`
- Test: `frontend/src/features/case/components/QuestionPrompt.test.tsx`

> `DiseasePicker`(select_button)는 Task 6에서 구현한다. 본 태스크에서는 먼저
> 임시로 select_button을 radio와 동일 처리하지 않도록, QuestionPrompt가
> Task 6 완료 전까지 select_button을 `null` 반환하지 않게 하기 위해 Task 6의
> import를 미리 넣는다(Task 6에서 파일 생성). **Task 5와 6은 순서대로 진행.**

- [ ] **Step 1: Chip 컴포넌트 작성**

`frontend/src/features/case/components/Chip.tsx`:
```tsx
import { cn } from '@/lib/utils';

interface ChipProps {
  label: string;
  selected?: boolean;
  disabled?: boolean;
  onClick: () => void;
}

export function Chip({ label, selected = false, disabled = false, onClick }: ChipProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'rounded-2xl px-4 py-2 text-sm font-medium ring-1 transition-colors disabled:opacity-50',
        selected
          ? 'bg-primary text-white ring-primary'
          : 'bg-canvas text-ink ring-line hover:bg-primary-tint'
      )}
    >
      {label}
    </button>
  );
}
```

- [ ] **Step 2: 실패하는 렌더 테스트 작성**

`frontend/src/features/case/components/QuestionPrompt.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { QuestionPrompt } from './QuestionPrompt';

describe('QuestionPrompt', () => {
  it('radio_button: 옵션 칩 클릭 시 question_id/value/label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'surgery',
          question_text: '수술도 받으셨나요?',
          input_type: 'radio_button',
          options: [
            { value: true, label: '예' },
            { value: false, label: '아니요' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '예' }));
    expect(onAnswer).toHaveBeenCalledWith('surgery', true, '예');
  });

  it('checkbox_button: 다중 선택 후 확인 시 배열 value와 합친 label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'treatment_items',
          question_text: '함께 받은 치료를 골라주세요.',
          input_type: 'checkbox_button',
          options: [
            { value: 'MRI_MRA', label: '영상검사' },
            { value: 'INJECTION', label: '주사치료' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '영상검사' }));
    await userEvent.click(screen.getByRole('button', { name: '주사치료' }));
    await userEvent.click(screen.getByRole('button', { name: '확인' }));
    expect(onAnswer).toHaveBeenCalledWith(
      'treatment_items',
      ['MRI_MRA', 'INJECTION'],
      '영상검사, 주사치료'
    );
  });

  it('text_input: 입력 후 전송 시 텍스트를 value/label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'annual_visit_count',
          question_text: '몇 번째 방문인가요?',
          input_type: 'text_input',
          placeholder: '예: 1번',
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.type(screen.getByPlaceholderText('예: 1번'), '3번');
    await userEvent.click(screen.getByRole('button', { name: '전송' }));
    expect(onAnswer).toHaveBeenCalledWith('annual_visit_count', '3번', '3번');
  });
});
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `pnpm test QuestionPrompt`
Expected: FAIL (QuestionPrompt / DiseasePicker 모듈 없음).

- [ ] **Step 4: QuestionPrompt 구현**

`frontend/src/features/case/components/QuestionPrompt.tsx`:
```tsx
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import type { AnswerValue, NextQuestion, NormalizedOption } from '../model';
import { normalizeOptions } from '../options';
import { Chip } from './Chip';
import { DiseasePicker } from './DiseasePicker';

interface QuestionPromptProps {
  question: NextQuestion;
  onAnswer: (questionId: string, value: AnswerValue, label: string) => void;
  disabled?: boolean;
}

interface InnerProps {
  question: NextQuestion;
  onAnswer: QuestionPromptProps['onAnswer'];
  disabled: boolean;
}

export function QuestionPrompt({ question, onAnswer, disabled = false }: QuestionPromptProps) {
  if (question.input_type === 'select_button') {
    return <DiseasePicker question={question} onAnswer={onAnswer} disabled={disabled} />;
  }
  if (question.input_type === 'checkbox_button') {
    return <CheckboxPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
  }
  if (question.input_type === 'text_input') {
    return <TextPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
  }
  return <RadioPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
}

function RadioPrompt({ question, onAnswer, disabled }: InnerProps) {
  const options = normalizeOptions(question.options);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(opt => (
        <Chip
          key={String(opt.value)}
          label={opt.label}
          disabled={disabled}
          onClick={() => onAnswer(question.question_id, opt.value, opt.label)}
        />
      ))}
    </div>
  );
}

function CheckboxPrompt({ question, onAnswer, disabled }: InnerProps) {
  const options = normalizeOptions(question.options);
  const [selected, setSelected] = useState<NormalizedOption[]>([]);

  const toggle = (opt: NormalizedOption) =>
    setSelected(prev =>
      prev.some(o => o.value === opt.value)
        ? prev.filter(o => o.value !== opt.value)
        : [...prev, opt]
    );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {options.map(opt => (
          <Chip
            key={String(opt.value)}
            label={opt.label}
            selected={selected.some(o => o.value === opt.value)}
            disabled={disabled}
            onClick={() => toggle(opt)}
          />
        ))}
      </div>
      <Button
        type="button"
        size="sm"
        className="self-start"
        disabled={disabled || selected.length === 0}
        onClick={() =>
          onAnswer(
            question.question_id,
            selected.map(o => o.value),
            selected.map(o => o.label).join(', ')
          )
        }
      >
        확인
      </Button>
    </div>
  );
}

function TextPrompt({ question, onAnswer, disabled }: InnerProps) {
  const [text, setText] = useState('');
  const submit = () => {
    const value = text.trim();
    if (!value) {
      return;
    }
    onAnswer(question.question_id, value, value);
    setText('');
  };
  return (
    <form
      className="flex gap-2"
      onSubmit={event => {
        event.preventDefault();
        submit();
      }}
    >
      <Input
        value={text}
        onChange={event => setText(event.target.value)}
        placeholder={question.placeholder ?? '입력해주세요'}
        disabled={disabled}
      />
      <Button type="submit" size="sm" disabled={disabled || !text.trim()}>
        전송
      </Button>
    </form>
  );
}
```

> 이 시점에 `./DiseasePicker` import가 미해결이라 테스트가 모듈 에러를 낼 수 있다.
> 곧바로 Task 6을 진행해 `DiseasePicker.tsx`를 생성한 뒤 본 태스크 테스트를 통과시킨다.

- [ ] **Step 5: (Task 6 완료 후) 테스트 통과 확인**

Run: `pnpm test QuestionPrompt`
Expected: PASS (3 passed). — DiseasePicker 생성 전이면 실패하므로 Task 6 Step 4 이후 재실행.

- [ ] **Step 6: Commit (Task 6과 함께)**

Chip/QuestionPrompt는 Task 6의 DiseasePicker와 의존하므로 **Task 6 완료 후 함께 커밋**한다(Task 6 Step 6).

---

## Task 6: `DiseasePicker` — 페이지네이션 + 직접입력 (TDD)

**Files:**
- Create: `frontend/src/features/case/components/DiseasePicker.tsx`
- Test: `frontend/src/features/case/components/DiseasePicker.test.tsx`

- [ ] **Step 1: 실패하는 테스트 작성**

`frontend/src/features/case/components/DiseasePicker.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import type { NextQuestion } from '../model';
import { DiseasePicker } from './DiseasePicker';

function makeQuestion(count: number): NextQuestion {
  return {
    question_id: 'disease_kcd',
    question_text: '가장 가까운 질병을 골라주세요.',
    input_type: 'select_button',
    options: Array.from({ length: count }, (_, i) => ({
      kcd: `K${i}`,
      name: `질병${i}`,
    })),
  };
}

describe('DiseasePicker', () => {
  it('첫 페이지에 후보 5개와 "해당 병명이 없어요" 칩을 노출한다', () => {
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={vi.fn()} />);

    expect(screen.getByRole('button', { name: '질병0' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '질병4' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '질병5' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '해당 병명이 없어요' })).toBeInTheDocument();
  });

  it('후보 칩 클릭 시 disease_kcd + kcd/name으로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={onAnswer} />);

    await userEvent.click(screen.getByRole('button', { name: '질병2' }));
    expect(onAnswer).toHaveBeenCalledWith('disease_kcd', 'K2', '질병2');
  });

  it('"해당 병명이 없어요"가 남은 페이지가 있으면 다음 5개로 이동한다', async () => {
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));
    expect(screen.getByRole('button', { name: '질병5' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '질병9' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '질병0' })).not.toBeInTheDocument();
  });

  it('마지막 페이지에서 "해당 병명이 없어요"를 누르면 직접 입력으로 전환되고 disease_name으로 전송한다', async () => {
    const onAnswer = vi.fn();
    render(<DiseasePicker question={makeQuestion(7)} onAnswer={onAnswer} />);

    // 7개 → 페이지0(0~4) + 페이지1(5~6). 한 번 누르면 페이지1, 두 번째에 직접입력.
    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));
    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));

    const input = screen.getByPlaceholderText('질병명을 직접 입력해주세요');
    await userEvent.type(input, '손목 인대 손상');
    await userEvent.click(screen.getByRole('button', { name: '전송' }));
    expect(onAnswer).toHaveBeenCalledWith('disease_name', '손목 인대 손상', '손목 인대 손상');
  });

  it('후보가 5개 이하면 "해당 병명이 없어요"가 바로 직접 입력으로 전환된다', async () => {
    render(<DiseasePicker question={makeQuestion(3)} onAnswer={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));
    expect(screen.getByPlaceholderText('질병명을 직접 입력해주세요')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test DiseasePicker`
Expected: FAIL (DiseasePicker 모듈 없음).

- [ ] **Step 3: DiseasePicker 구현**

`frontend/src/features/case/components/DiseasePicker.tsx`:
```tsx
import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import type { AnswerValue, NextQuestion } from '../model';
import { normalizeOptions } from '../options';
import { Chip } from './Chip';

const PAGE_SIZE = 5;
const NONE_LABEL = '해당 병명이 없어요';

interface DiseasePickerProps {
  question: NextQuestion;
  onAnswer: (questionId: string, value: AnswerValue, label: string) => void;
  disabled?: boolean;
}

export function DiseasePicker({ question, onAnswer, disabled = false }: DiseasePickerProps) {
  const options = useMemo(() => normalizeOptions(question.options), [question.options]);
  const [page, setPage] = useState(0);
  const [directInput, setDirectInput] = useState(false);
  const [text, setText] = useState('');

  const start = page * PAGE_SIZE;
  const pageOptions = options.slice(start, start + PAGE_SIZE);
  const hasMore = start + PAGE_SIZE < options.length;

  const handleNone = () => {
    if (hasMore) {
      setPage(prev => prev + 1);
    } else {
      setDirectInput(true);
    }
  };

  if (directInput) {
    const submit = () => {
      const value = text.trim();
      if (!value) {
        return;
      }
      onAnswer('disease_name', value, value);
      setText('');
    };
    return (
      <form
        className="flex gap-2"
        onSubmit={event => {
          event.preventDefault();
          submit();
        }}
      >
        <Input
          value={text}
          onChange={event => setText(event.target.value)}
          placeholder="질병명을 직접 입력해주세요"
          disabled={disabled}
        />
        <Button type="submit" size="sm" disabled={disabled || !text.trim()}>
          전송
        </Button>
      </form>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {pageOptions.map(opt => (
        <Chip
          key={String(opt.value)}
          label={opt.label}
          disabled={disabled}
          onClick={() => onAnswer('disease_kcd', opt.value, opt.label)}
        />
      ))}
      <Chip label={NONE_LABEL} disabled={disabled} onClick={handleNone} />
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인 (DiseasePicker + QuestionPrompt)**

Run: `pnpm test DiseasePicker QuestionPrompt`
Expected: PASS (DiseasePicker 5 + QuestionPrompt 3 = 8 passed).

- [ ] **Step 5: 전체 테스트 + 빌드 확인**

Run: `pnpm test && pnpm build`
Expected: 모든 테스트 PASS, build 성공.

- [ ] **Step 6: Commit (Task 5 + 6 함께)**

```bash
git add frontend/src/features/case/components/
git commit -m "feat(frontend): next_question 렌더러(QuestionPrompt/DiseasePicker/Chip) 추가"
```

---

## Task 7: `Chatbot.tsx`에 연결

**Files:**
- Modify: `frontend/src/features/home/components/Chatbot.tsx`

흐름/렌더 로직을 훅·컴포넌트로 옮겼으므로 Chatbot은 연결만 한다. 기존
`toBotMessages`와 내부 상태/`send` 로직을 제거한다. UI(빌드·수동)로 검증한다.

- [ ] **Step 1: Chatbot.tsx 전체 교체**

`frontend/src/features/home/components/Chatbot.tsx` 전체를 아래로 교체:
```tsx
import { AnimatePresence, motion } from 'framer-motion';
import { Bot, Lock, SendHorizontal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { QuestionPrompt } from '@/features/case/components/QuestionPrompt';
import { useChatFlow } from '@/features/case/useChatFlow';
import { cn } from '@/lib/utils';

const GREETING = '안녕하세요! 보장zip AI 챗봇이에요 🙂 어떤 도움이 필요하신가요?';

interface ChatbotProps {
  className?: string;
  /** 전제 조건 미충족 시 입력 잠금 (보험 선택/ PDF 업로드 전). */
  locked?: boolean;
  /** 선택한 보험 상품 id. `/cases` 생성 요청의 policy_ids로 전달한다. */
  selectedPolicyIds: string[];
  /** 최초 케이스 생성 완료 후 상위 화면에 상태를 공유한다. */
  onCaseCreated?: (caseId: string, selectedPolicyIds: string[]) => void;
}

/** "챗봇" — next_question 기반 단계형 대화. */
export function Chatbot({
  className,
  locked = false,
  selectedPolicyIds,
  onCaseCreated,
}: ChatbotProps) {
  const { messages, caseId, pendingQuestion, submitting, error, done, start, answer } = useChatFlow(
    { selectedPolicyIds, onCaseCreated }
  );
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // 새 메시지/질문이 추가되면 항상 맨 아래로 스크롤.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, pendingQuestion]);

  const started = caseId !== null;
  const inputDisabled = locked || submitting || started;

  const handleSend = () => {
    if (inputDisabled) {
      return;
    }
    const value = input.trim();
    if (!value) {
      return;
    }
    setInput('');
    void start(value);
  };

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6',
        className
      )}
    >
      <h2 className="shrink-0 text-lg font-bold text-ink">챗봇</h2>

      {locked && messages.length === 0 ? (
        <div className="mt-5 flex min-h-0 flex-1 flex-col items-center justify-center gap-3 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-canvas text-muted">
            <Lock className="size-6" />
          </span>
          <div>
            <p className="text-sm font-semibold text-ink">먼저 분석할 보험을 선택해주세요</p>
            <p className="mt-1 text-sm leading-6 text-muted">
              보험을 선택하거나 약관 PDF를 올리면
              <br />
              상황 입력을 시작할 수 있어요.
            </p>
          </div>
        </div>
      ) : (
        <div
          ref={scrollRef}
          className="scrollbar-hide mt-5 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto"
        >
          {/* 봇 인사 */}
          <motion.div
            className="flex items-start gap-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
              <Bot className="size-5" />
            </span>
            <p className="rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-ink">
              {GREETING}
            </p>
          </motion.div>

          {/* 대화 내역 */}
          <AnimatePresence initial={false}>
            {messages.map((message, index) => (
              <motion.div
                key={`${message.role}-${index}`}
                layout
                initial={{ opacity: 0, y: 10, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 500, damping: 32 }}
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6',
                  message.role === 'user'
                    ? 'self-end rounded-tr-sm bg-primary text-white'
                    : 'self-start rounded-tl-sm bg-canvas text-ink'
                )}
              >
                {message.text}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* 현재 질문에 대한 입력 컨트롤 */}
          {pendingQuestion && !done && (
            <div className="mt-1">
              <QuestionPrompt
                question={pendingQuestion}
                onAnswer={answer}
                disabled={submitting}
              />
            </div>
          )}

          {submitting && (
            <p className="self-start rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-muted">
              입력해주신 내용을 분석하고 있습니다.
            </p>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
      )}

      <div className="mt-6 shrink-0">
        <form
          className="relative"
          onSubmit={event => {
            event.preventDefault();
            handleSend();
          }}
        >
          <Input
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder={
              locked
                ? '보험을 먼저 선택해주세요'
                : started
                  ? '아래 선택지에서 답해주세요'
                  : '메시지를 입력하세요...'
            }
            className="pr-12"
            disabled={inputDisabled}
          />
          <Button
            type="submit"
            variant="ghost"
            size="icon"
            disabled={inputDisabled}
            className="absolute right-1 top-1/2 size-9 -translate-y-1/2 text-primary hover:bg-primary-tint"
            aria-label="메시지 전송"
          >
            <SendHorizontal />
          </Button>
        </form>
        <p className="mt-3 text-center text-xs leading-5 text-muted">
          ※ 챗봇의 답변은 참고용이며, 실제 보장 여부는 약관 및 상황에 따라 달라질 수 있습니다.
        </p>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: lint + build 확인**

Run: `pnpm lint && pnpm build`
Expected: 통과. `CreateCaseResponse`/`toBotMessages` 미사용 import가 남아 있으면 제거(위 전체 교체로 이미 제거됨).

- [ ] **Step 3: 수동 확인 (개발 서버)**

Run: `pnpm dev` → http://localhost:5173
확인:
1. 보험 선택 후 상황 입력 → 봇이 질병 후보 칩 5개 + "해당 병명이 없어요" 노출.
2. 후보 칩 클릭 → 다음 질문(예/아니요·치료항목·입력창 등)으로 진행.
3. "해당 병명이 없어요" → (후보 6개 이상이면) 다음 5개, 마지막엔 직접입력창.
4. 모든 질문 종료 시 마무리 봇 메시지 노출.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/home/components/Chatbot.tsx
git commit -m "feat(frontend): 챗봇을 next_question 단계형 대화로 연결"
```

---

## Self-Review 결과 (작성자 점검)

- **Spec 커버리지:** 데이터 계약(2절)→T2, 정규화(2절)→T3, useChatFlow 흐름(3.1)→T4,
  QuestionPrompt 분기(3.2)→T5, 질병 페이지네이션+직접입력(4절)→T6, 종료/검수
  플레이스홀더(5절)→T4(`DONE_MESSAGE`)+T7, 에러/엣지(6절)→T4·T6, 테스트(7절)→T3·T4·T5·T6.
- **백엔드 의존(9절):** 질병 후보 전체 전송(`[:5]` 제거)은 백엔드 병행 작업. 미완 시
  1페이지만 노출되고 "해당 병명 없음"→직접입력으로 안전 동작(코드 변경 불필요).
- **타입 일관성:** `AnswerValue`(T2)·`NormalizedOption`(T2)·`normalizeOptions`(T3)·
  `useChatFlow`(T4)·`QuestionPrompt`/`DiseasePicker`(T5·T6) 시그니처 일치 확인.
- **검수 폼:** 범위 밖 — 종료 시 봇 마무리 메시지(`DONE_MESSAGE`)까지만(스펙 5절과 일치).
