# 랜딩페이지 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 서비스(보장체크)의 첫 진입점이 될 정적 랜딩페이지를 `/`에 추가하고, 기존 보험 등록 화면을 `/home`으로 이동한다.

**Architecture:** `frontend/src/features/landing/` 아래에 섹션별 컴포넌트를 만들고 `pages/LandingPage.tsx`에서 조립한다. 히어로 우측은 단순화된 미니 UI 흐름 애니메이션, 2페이지는 시나리오 무한 마퀴, 3페이지는 핵심 가치 3카드, 하단은 footer. 백엔드 호출 없음(정적). CTA는 모두 `/home`으로 라우팅.

**Tech Stack:** React 19, TypeScript, Tailwind 4(`@theme` 토큰), framer-motion ^12, lucide-react ^1.21, react-router-dom ^7. 기존 `cn` 유틸과 `Button`(asChild 지원) 재사용.

**검증 방식(중요):** 이 프론트엔드에는 테스트 러너가 없다(vitest/jest 미설치). CI 게이트는 `pnpm lint && pnpm build`(tsc 타입체크 포함)이다. 따라서 각 태스크의 검증은 **`pnpm lint`(필요 시) + `pnpm build`** 통과와 **수동 브라우저 확인**으로 한다. 정적 마케팅 페이지를 위해 테스트 하니스를 새로 도입하지 않는다(YAGNI).

**공통 규약:**
- 모든 명령은 `frontend/` 디렉터리에서 실행. (`cd frontend` 후 실행하거나 `frontend`가 cwd인 상태)
- import 별칭 `@` → `frontend/src`.
- 색상은 기존 토큰(`primary`, `primary-soft`, `primary-tint`, `canvas`, `surface`, `ink`, `muted`, `line`, `success`, `success-tint`)만 사용. 새 색상 도입 금지.
- 커밋 메시지는 한국어 Conventional Commits, scope `frontend`.

**커밋 전략(페이지 단위):** 태스크마다 커밋하지 않고 **3페이지 단위로 3커밋**한다. 각 태스크에서
`pnpm lint && pnpm build`로 검증만 하고, 아래 페이지 경계에서만 커밋한다.
- **커밋 1 — 1페이지(히어로 + 라우팅):** Task 1 · 3 · 4 · 5 완료 후 (Task 5 끝에서 커밋)
- **커밋 2 — 2페이지(시나리오 마퀴):** Task 2 · 6 완료 후 (Task 6 끝에서 커밋)
- **커밋 3 — 3페이지(핵심 가치 + footer + 조립):** Task 7 · 8 · 9 완료 후 (Task 9 끝에서 커밋)

---

## File Structure

생성:
- `frontend/src/pages/LandingPage.tsx` — 랜딩 페이지 조립
- `frontend/src/features/landing/data/scenarios.ts` — 시나리오 카드 데이터
- `frontend/src/features/landing/components/RotatingHeadline.tsx` — 제목 로테이트
- `frontend/src/features/landing/components/HeroFlowAnimation.tsx` — 히어로 우측 미니 UI 흐름
- `frontend/src/features/landing/components/HeroSection.tsx` — 1페이지 히어로
- `frontend/src/features/landing/components/ScenarioCard.tsx` — 시나리오 카드
- `frontend/src/features/landing/components/ScenarioSection.tsx` — 2페이지 마퀴
- `frontend/src/features/landing/components/ValueSection.tsx` — 3페이지 핵심 가치
- `frontend/src/features/landing/components/LandingFooter.tsx` — footer

수정:
- `frontend/src/App.tsx` — `/` → LandingPage, 기존 홈을 `/home`으로
- `frontend/src/pages/ResultPage.tsx` — `navigate('/')` 3곳을 `navigate('/home')`으로

---

## Task 1: 라우팅 변경 + 플레이스홀더 LandingPage

기존 `/`(HomePage)를 `/home`으로 옮기고, `/`에 새 LandingPage를 연결한다. 결과 페이지의 "처음으로" 이동도 `/home`으로 맞춘다. 먼저 최소 플레이스홀더로 라우팅이 동작하는지 확인한 뒤, 이후 태스크에서 섹션을 채운다.

**Files:**
- Create: `frontend/src/pages/LandingPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/pages/ResultPage.tsx:146,173,176`

- [ ] **Step 1: 플레이스홀더 LandingPage 생성**

`frontend/src/pages/LandingPage.tsx`:

```tsx
import { AppHeader } from '@/components/common/AppHeader';

/** 서비스 소개 랜딩페이지 (루트 진입점). 섹션은 후속 태스크에서 채운다. */
export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <AppHeader />
      <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-10 sm:px-8">
        <p className="text-muted">랜딩페이지 준비 중</p>
      </main>
    </div>
  );
}

export default LandingPage;
```

- [ ] **Step 2: App.tsx 라우트 변경**

`frontend/src/App.tsx`에서 import에 `LandingPage`를 추가하고 라우트를 조정한다. 변경 후 전체 파일:

```tsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AuthModal } from '@/features/auth/components/AuthModal';
import { LandingPage } from '@/pages/LandingPage';
import { HomePage } from '@/pages/HomePage';
import { ConfirmPage } from '@/pages/ConfirmPage';
import { ResultPage } from '@/pages/ResultPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/cases/:caseId/confirm" element={<ConfirmPage />} />
        <Route path="/cases/:caseId/result" element={<ResultPage />} />
      </Routes>
      <AuthModal />
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 3: ResultPage의 "처음으로" 이동을 /home으로 변경**

`frontend/src/pages/ResultPage.tsx`에서 `navigate('/')` 3곳을 모두 `navigate('/home')`으로 바꾼다.
- 146행 `onRestart={() => navigate('/')}` → `onRestart={() => navigate('/home')}`
- 173행 `onClick={() => navigate('/')}` → `onClick={() => navigate('/home')}`
- 176행 `onClick={() => navigate('/')}` → `onClick={() => navigate('/home')}`

(AppHeader 로고의 `Link to="/"`는 랜딩으로 가는 것이 맞으므로 변경하지 않는다.)

- [ ] **Step 4: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 에러 없이 통과(타입체크 포함).

- [ ] **Step 5: 수동 확인**

Run: `pnpm dev` 후 브라우저에서
- `http://localhost:5173/` → "랜딩페이지 준비 중" + AppHeader 표시
- `http://localhost:5173/home` → 기존 보험 등록 화면 표시
Expected: 위 두 경로가 의도대로 렌더.

- [ ] **Step 6: 커밋 보류**

이 태스크는 1페이지 그룹에 속한다. **커밋하지 않고** Task 5 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 2: 시나리오 데이터 모듈

2페이지 마퀴에 쓸 질문형 시나리오 텍스트를 코드와 분리한다.

**Files:**
- Create: `frontend/src/features/landing/data/scenarios.ts`

- [ ] **Step 1: 데이터 모듈 작성**

`frontend/src/features/landing/data/scenarios.ts`:

```ts
/** 랜딩 2페이지 마퀴에 노출할 질문형 시나리오. (정적 마케팅 데이터) */
export interface Scenario {
  id: string;
  /** 사용자 상황/질문 한 줄. */
  question: string;
  /** 카드 보조 태그(질병/상황 분류). */
  tag: string;
}

export const SCENARIOS: Scenario[] = [
  { id: 'disc', question: '허리디스크로 입원했어요. 청구가 가능할까요?', tag: '입원' },
  { id: 'fracture', question: '계단에서 넘어져 골절됐는데 보장되나요?', tag: '상해' },
  { id: 'cancer', question: '갑상선암 진단을 받았어요. 받을 수 있는 보험금이 있을까요?', tag: '진단' },
  { id: 'surgery', question: '백내장 수술을 했는데 청구할 수 있나요?', tag: '수술' },
  { id: 'childbirth', question: '제왕절개로 출산했어요. 특약으로 보장되나요?', tag: '출산' },
  { id: 'pet', question: '반려견 치료비도 청구 대상이 되나요?', tag: '특약' },
  { id: 'dental', question: '임플란트 치료, 놓친 치아 보장이 있는지 궁금해요.', tag: '치과' },
  { id: 'mental', question: '공황장애로 통원 치료 중인데 청구 가능할까요?', tag: '통원' },
];
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 커밋 보류**

이 태스크는 2페이지 그룹에 속한다. **커밋하지 않고** Task 6 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 3: RotatingHeadline 컴포넌트

히어로 제목 둘째 줄에서 3개 문구를 순환시킨다.

**Files:**
- Create: `frontend/src/features/landing/components/RotatingHeadline.tsx`

- [ ] **Step 1: 컴포넌트 작성**

`frontend/src/features/landing/components/RotatingHeadline.tsx`:

```tsx
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';

import { cn } from '@/lib/utils';

const PHRASES = ['놓친 보장이 있는지', '받을 수 있는 보험금이 있는지', '청구 가능한 특약이 있는지'];

const INTERVAL_MS = 2500;

interface RotatingHeadlineProps {
  className?: string;
}

/** 히어로 제목 둘째 줄 — 문구 3개를 순환 표시. */
export function RotatingHeadline({ className }: RotatingHeadlineProps) {
  const reduceMotion = useReducedMotion();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (reduceMotion) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex(prev => (prev + 1) % PHRASES.length);
    }, INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [reduceMotion]);

  return (
    <span className={cn('relative block text-primary', className)} aria-live="polite">
      <AnimatePresence mode="wait">
        <motion.span
          key={index}
          className="block"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          {PHRASES[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 커밋 보류**

1페이지 그룹. **커밋하지 않고** Task 5 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 4: HeroFlowAnimation 컴포넌트

서비스 흐름을 단순화된 미니 UI로 재현한다. **결과 화면이 이 서비스의 핵심**이므로 상단 탭 2개(청구가능 Case1 / 추가보장찾기 Case2)로 케이스를 골라, 선택한 케이스의 3단계(홈→상황 확인→분석 결과)를 자동 순환한다. 결과 단계는 Case1=금액 카운트업, Case2=성장 막대 그래프로 다르게 표현한다. 탭을 바꾸면 "홈"부터 다시 시작. 기본 Case1. 실제 페이지 컴포넌트는 재사용하지 않되, 결과 표현은 실제 화면의 색·구조를 따른다.

작은 카운트업 훅을 먼저 만들고(Step 1), 메인 컴포넌트를 작성한다(Step 2).

**Files:**
- Create: `frontend/src/features/landing/components/useCountUp.ts`
- Create: `frontend/src/features/landing/components/HeroFlowAnimation.tsx`

- [ ] **Step 1: 카운트업 훅 작성**

`frontend/src/features/landing/components/useCountUp.ts`:

```ts
import { useEffect, useRef, useState } from 'react';

/**
 * `active`가 true가 되면 0 → target까지 duration 동안 카운트업한다.
 * `instant`(reduce-motion 등)이면 즉시 target 값으로 고정.
 */
export function useCountUp(target: number, active: boolean, instant: boolean, durationMs = 1100) {
  const [value, setValue] = useState(instant ? target : 0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (instant) {
      setValue(target);
      return;
    }
    if (!active) {
      setValue(0);
      return;
    }

    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      // easeOut(cubic)으로 룰렛 감속 느낌.
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };
    frameRef.current = requestAnimationFrame(tick);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [target, active, instant, durationMs]);

  return value;
}
```

- [ ] **Step 2: 메인 컴포넌트 작성**

`frontend/src/features/landing/components/HeroFlowAnimation.tsx`:

```tsx
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { Bot, CheckCircle2, Sparkles, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

import { cn } from '@/lib/utils';
import { useCountUp } from '@/features/landing/components/useCountUp';

type CaseKey = 'case1' | 'case2';
type StepKey = 'home' | 'confirm' | 'result';

const STEP_ORDER: StepKey[] = ['home', 'confirm', 'result'];

// 결과 단계는 연출을 보여줄 수 있게 더 길게 머문다.
const STEP_HOLD_MS: Record<StepKey, number> = {
  home: 3400,
  confirm: 2600,
  result: 4000,
};

// 케이스별 탭 정의.
const CASES: { key: CaseKey; label: string }[] = [
  { key: 'case1', label: '청구가능' },
  { key: 'case2', label: '추가보장찾기' },
];

// 케이스별 홈 단계 타이핑 질문.
const TYPING_TARGET: Record<CaseKey, string> = {
  case1: '허리디스크로 입원했어요. 청구가 가능할까요?',
  case2: '받을 수 있는 보장을 더 찾고 싶어요.',
};

const TYPING_SPEED_MS = 55;

const STEP_LABEL: Record<StepKey, string> = {
  home: '1 · 상황 입력',
  confirm: '2 · 상황 확인',
  result: '3 · 분석 결과',
};

// Case1 금액, Case2 그래프 수치 (실제 mock 톤에 맞춘 예시값).
const PAYABLE_AMOUNT = 612000;
const CURRENT_AMOUNT = 480000;
const EXPECTED_AMOUNT = 760000;

function formatWon(value: number) {
  return value.toLocaleString('ko-KR');
}

/** 히어로 우측: 탭으로 케이스를 골라 그 흐름(입력→확인→결과)을 미니 UI로 순환 재현. */
export function HeroFlowAnimation({ className }: { className?: string }) {
  const reduceMotion = useReducedMotion() ?? false;
  const [caseKey, setCaseKey] = useState<CaseKey>('case1');
  // reduce-motion이면 결과 단계를 바로 보여준다.
  const [stepIndex, setStepIndex] = useState(reduceMotion ? STEP_ORDER.length - 1 : 0);
  const [typed, setTyped] = useState(reduceMotion ? TYPING_TARGET.case1 : '');

  const step = STEP_ORDER[stepIndex];

  // 금액 카운트업 (case1 결과 단계 진입 시 동작).
  const payable = useCountUp(PAYABLE_AMOUNT, caseKey === 'case1' && step === 'result', reduceMotion);

  // 탭 변경 시 흐름을 홈부터 재시작.
  const selectCase = (next: CaseKey) => {
    setCaseKey(next);
    setStepIndex(reduceMotion ? STEP_ORDER.length - 1 : 0);
    setTyped(reduceMotion ? TYPING_TARGET[next] : '');
  };

  // 단계 자동 순환 (reduce-motion이면 정지). 단계별 체류 시간이 다르므로 setTimeout 체인.
  useEffect(() => {
    if (reduceMotion) {
      return;
    }
    const timer = window.setTimeout(() => {
      setStepIndex(prev => (prev + 1) % STEP_ORDER.length);
    }, STEP_HOLD_MS[step]);
    return () => window.clearTimeout(timer);
  }, [step, caseKey, reduceMotion]);

  // 홈 단계 진입 시 타자기 효과 (케이스별 질문).
  useEffect(() => {
    if (reduceMotion || step !== 'home') {
      return;
    }
    const target = TYPING_TARGET[caseKey];
    setTyped('');
    let i = 0;
    const timer = window.setInterval(() => {
      i += 1;
      setTyped(target.slice(0, i));
      if (i >= target.length) {
        window.clearInterval(timer);
      }
    }, TYPING_SPEED_MS);
    return () => window.clearInterval(timer);
  }, [step, caseKey, reduceMotion]);

  // Case2 그래프 막대 비율.
  const currentRatio = (CURRENT_AMOUNT / EXPECTED_AMOUNT) * 100;
  const addedRatio = 100 - currentRatio;

  return (
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-card bg-surface p-5 shadow-lg ring-1 ring-line',
        className
      )}
    >
      {/* 케이스 선택 탭 */}
      <div className="mb-4 flex gap-1 rounded-xl bg-canvas p-1">
        {CASES.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => selectCase(key)}
            className={cn(
              'flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition-colors',
              caseKey === key ? 'bg-surface text-primary shadow-sm' : 'text-muted hover:text-ink'
            )}
            aria-pressed={caseKey === key}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mb-4 flex items-center gap-2 text-xs font-semibold text-primary">
        <Sparkles className="size-4" />
        {STEP_LABEL[step]}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${caseKey}-${step}`}
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="min-h-65"
        >
          {step === 'home' && (
            <div className="flex flex-col gap-3">
              <div className="flex items-start gap-2">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
                  <Bot className="size-4" />
                </span>
                <p className="rounded-2xl rounded-tl-sm bg-canvas px-3 py-2 text-xs leading-5 text-ink">
                  어떤 상황인지 편하게 적어주세요 🙂
                </p>
              </div>
              <div className="ml-auto max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-3 py-2 text-xs leading-5 text-white">
                {typed}
                <span className="ml-0.5 inline-block w-0.5 animate-pulse bg-white/80">&nbsp;</span>
              </div>
            </div>
          )}

          {step === 'confirm' && (
            <div className="flex flex-col gap-2">
              {[
                ['가입 보험', '○○생명 건강보험'],
                ['질병', '허리디스크 (M51)'],
                ['치료', '입원 8일'],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between rounded-xl border border-line bg-canvas/60 px-3 py-2 text-xs"
                >
                  <span className="text-muted">{label}</span>
                  <span className="font-semibold text-ink">{value}</span>
                </div>
              ))}
            </div>
          )}

          {/* 결과 — Case1: 청구 가능 보장 (금액 카운트업, 룰렛 느낌) */}
          {step === 'result' && caseKey === 'case1' && (
            <div className="flex flex-col gap-3">
              <div className="rounded-xl bg-canvas/70 px-4 py-4 text-center">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-success">
                  <CheckCircle2 className="size-4" />
                  청구 가능 보장 2건을 찾았어요
                </div>
                <p className="mt-1 text-[11px] font-semibold text-muted">예상 보험금</p>
                <p className="mt-1 text-3xl font-black tabular-nums text-primary">
                  {formatWon(payable)}
                  <span className="ml-0.5 text-base font-black text-ink">원</span>
                </p>
              </div>
              {['입원일당 특약', '질병수술비 특약'].map(name => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded-xl border border-line px-3 py-2 text-xs"
                >
                  <span className="font-medium text-ink">{name}</span>
                  <span className="font-semibold text-primary">청구 가능</span>
                </div>
              ))}
            </div>
          )}

          {/* 결과 — Case2: 추가 보장 찾기 (성장 막대 그래프) */}
          {step === 'result' && caseKey === 'case2' && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-1.5 text-xs font-bold text-primary">
                <TrendingUp className="size-4" />
                조건을 채우면 더 받을 수 있어요
              </div>
              <div className="flex items-end justify-center gap-6 rounded-xl bg-canvas/70 px-4 pb-3 pt-4">
                {/* 현재 막대 */}
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-32 items-end">
                    <motion.div
                      className="w-12 rounded-t-md bg-[#bfe5df]"
                      initial={reduceMotion ? false : { height: 0 }}
                      animate={{ height: `${(CURRENT_AMOUNT / EXPECTED_AMOUNT) * 8}rem` }}
                      transition={{ duration: 0.7, ease: 'easeOut' }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-muted">현재</span>
                  <span className="text-xs font-bold text-ink">{formatWon(CURRENT_AMOUNT)}원</span>
                </div>
                {/* 조건 충족 시 막대 (상단 추가분 강조) */}
                <div className="flex flex-col items-center gap-2">
                  <motion.div
                    className="flex w-12 flex-col-reverse overflow-hidden rounded-t-md"
                    initial={reduceMotion ? false : { height: 0 }}
                    animate={{ height: '8rem' }}
                    transition={{ duration: 0.7, ease: 'easeOut' }}
                  >
                    <div className="bg-[#bfe5df]" style={{ height: `${currentRatio}%` }} />
                    <div className="bg-[#18c9b5]" style={{ height: `${addedRatio}%` }} />
                  </motion.div>
                  <span className="text-[10px] font-semibold text-primary">조건 충족 시</span>
                  <span className="text-xs font-black text-primary">
                    {formatWon(EXPECTED_AMOUNT)}원
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* 단계 인디케이터 */}
      <div className="mt-4 flex gap-1.5">
        {STEP_ORDER.map((key, i) => (
          <span
            key={key}
            className={cn(
              'h-1.5 flex-1 rounded-full transition-colors',
              i === stepIndex ? 'bg-primary' : 'bg-line'
            )}
          />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 4: 수동 확인 (선택)**

`HeroSection` 조립(Task 5) 후 함께 확인 가능. 탭이 "청구가능/추가보장찾기" 2개로 나오고,
청구가능 탭은 결과에서 금액이 0→612,000원 카운트업, 추가보장찾기 탭은 결과에서 두 막대가
차오르는지 확인. 탭 전환 시 흐름이 홈부터 재시작하는지 확인.

- [ ] **Step 5: 커밋 보류**

1페이지 그룹. **커밋하지 않고** Task 5 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 5: HeroSection 컴포넌트

배지 + 제목(RotatingHeadline) + CTA 2개 + 우측 HeroFlowAnimation을 조립한다.

**Files:**
- Create: `frontend/src/features/landing/components/HeroSection.tsx`

- [ ] **Step 1: 컴포넌트 작성**

`frontend/src/features/landing/components/HeroSection.tsx`:

```tsx
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { HeroFlowAnimation } from '@/features/landing/components/HeroFlowAnimation';
import { RotatingHeadline } from '@/features/landing/components/RotatingHeadline';

/** 1페이지: 히어로 (카피 + CTA + 흐름 애니메이션). */
export function HeroSection() {
  return (
    <section className="bg-linear-to-b from-surface to-primary-tint">
      <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(360px,440px)] lg:py-24">
        <div className="flex flex-col gap-6">
          <span className="inline-flex w-fit items-center rounded-full bg-primary-tint px-3 py-1 text-xs font-semibold text-primary">
            AI가 찾아주는 내 보험의 숨은 혜택
          </span>

          <h1 className="text-4xl font-extrabold leading-tight text-ink sm:text-5xl">
            이미 낸 보험료
            <RotatingHeadline className="mt-1" />
          </h1>

          <p className="text-base text-muted">어떤 도움이 필요하신가요?</p>

          <div className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/home">
                청구가능보험 확인하기
                <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/home">
                추가보장찾기 시작하기
                <ArrowRight />
              </Link>
            </Button>
          </div>
        </div>

        <HeroFlowAnimation className="w-full" />
      </div>
    </section>
  );
}
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 1페이지 커밋 (Task 1·3·4·5 일괄)**

1페이지(히어로 + 라우팅) 작업을 한 번에 커밋한다.

```bash
git add frontend/src/App.tsx \
  frontend/src/pages/ResultPage.tsx \
  frontend/src/pages/LandingPage.tsx \
  frontend/src/features/landing/components/RotatingHeadline.tsx \
  frontend/src/features/landing/components/useCountUp.ts \
  frontend/src/features/landing/components/HeroFlowAnimation.tsx \
  frontend/src/features/landing/components/HeroSection.tsx
git commit -m "feat(frontend): 랜딩 히어로 섹션 및 라우트 추가"
```

(주의: 이 시점에 Task 2의 `scenarios.ts`가 미리 작성돼 있을 수 있다. 위 `git add`는 1페이지
파일만 명시하므로 `scenarios.ts`는 스테이징되지 않고 2페이지 커밋에서 올라간다.)

---

## Task 6: ScenarioCard + ScenarioSection (무한 마퀴)

질문형 시나리오 카드를 가로 무한 스크롤로 순환시킨다. 마퀴 keyframe을 `index.css`에 추가하고, 카드 목록을 2배 복제해 끊김 없이 이어붙인다. hover 시 일시정지, reduce-motion이면 정지.

**Files:**
- Create: `frontend/src/features/landing/components/ScenarioCard.tsx`
- Create: `frontend/src/features/landing/components/ScenarioSection.tsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: index.css에 마퀴 keyframe/유틸 추가**

`frontend/src/index.css`의 `@utility animate-coverage-bar-rise { ... }` 블록 바로 뒤(180행 부근, `@layer base` 시작 전)에 다음을 추가한다:

```css
@keyframes marquee-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

@utility animate-marquee {
  animation: marquee-scroll 40s linear infinite;
}
```

그리고 기존 `@media (prefers-reduced-motion: reduce)` 블록(301행 부근, `@layer components` 안)의 셀렉터에 `.animate-marquee`를 추가한다. 변경 후:

```css
  @media (prefers-reduced-motion: reduce) {
    .animate-result-enter,
    .animate-coverage-bar-rise,
    .animate-marquee {
      animation: none;
    }
  }
```

- [ ] **Step 2: ScenarioCard 작성**

`frontend/src/features/landing/components/ScenarioCard.tsx`:

```tsx
import { MessageCircleQuestion } from 'lucide-react';

import type { Scenario } from '@/features/landing/data/scenarios';

/** 마퀴에 표시할 질문형 시나리오 단일 카드. */
export function ScenarioCard({ scenario }: { scenario: Scenario }) {
  return (
    <div className="flex w-80 shrink-0 flex-col gap-3 rounded-card bg-surface p-5 shadow-sm ring-1 ring-line">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-full bg-primary-tint text-primary">
          <MessageCircleQuestion className="size-4" />
        </span>
        <span className="rounded-full bg-canvas px-2 py-0.5 text-xs font-medium text-muted">
          {scenario.tag}
        </span>
      </div>
      <p className="text-sm font-semibold leading-6 text-ink">{scenario.question}</p>
    </div>
  );
}
```

- [ ] **Step 3: ScenarioSection 작성**

`frontend/src/features/landing/components/ScenarioSection.tsx`:

```tsx
import { ScenarioCard } from '@/features/landing/components/ScenarioCard';
import { SCENARIOS } from '@/features/landing/data/scenarios';

/** 2페이지: 질문형 시나리오 무한 마퀴. */
export function ScenarioSection() {
  // 끊김 없는 루프를 위해 목록을 2배로 복제 (translateX(-50%) 기준).
  const loop = [...SCENARIOS, ...SCENARIOS];

  return (
    <section className="bg-canvas py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 text-center sm:px-8">
        <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">
          이런 상황, <span className="text-primary">청구 가능할까요?</span>
        </h2>
        <p className="mt-3 text-sm text-muted sm:text-base">
          실제로 많이 묻는 상황들이에요. 내 경우도 청구할 수 있는지 확인해보세요.
        </p>
      </div>

      <div className="group mt-10 overflow-hidden">
        <div className="animate-marquee flex w-max gap-5 group-hover:[animation-play-state:paused]">
          {loop.map((scenario, index) => (
            <ScenarioCard key={`${scenario.id}-${index}`} scenario={scenario} />
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 5: 수동 확인**

`pnpm dev`에서 ScenarioSection을 임시로 확인할 수 있으나, LandingPage 조립(Task 9) 후 함께 확인해도 된다. 최소한 빌드 통과를 확인한다.

- [ ] **Step 6: 2페이지 커밋 (Task 2·6 일괄)**

2페이지(시나리오 마퀴) 작업을 한 번에 커밋한다. Task 2의 데이터 모듈도 함께 올린다.

```bash
git add frontend/src/features/landing/data/scenarios.ts \
  frontend/src/features/landing/components/ScenarioCard.tsx \
  frontend/src/features/landing/components/ScenarioSection.tsx \
  frontend/src/index.css
git commit -m "feat(frontend): 시나리오 무한 마퀴 섹션 추가"
```

---

## Task 7: ValueSection (핵심 가치 3카드)

**Files:**
- Create: `frontend/src/features/landing/components/ValueSection.tsx`

- [ ] **Step 1: 컴포넌트 작성**

`frontend/src/features/landing/components/ValueSection.tsx`:

```tsx
import { FileText, ShieldCheck, Sparkles } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface ValueItem {
  icon: LucideIcon;
  title: string;
  desc: string;
}

const VALUES: ValueItem[] = [
  {
    icon: FileText,
    title: '약관 원문 근거',
    desc: '분석 결과를 약관 원문과 함께 보여드려요. 근거 없는 추정은 하지 않습니다.',
  },
  {
    icon: ShieldCheck,
    title: 'AI 환각 방지',
    desc: '약관 원문 컨텍스트 안에서만 분석해, 사실과 다른 답을 막습니다.',
  },
  {
    icon: Sparkles,
    title: '무료 · 간편',
    desc: '보험을 고르거나 약관을 올리기만 하면, 놓친 보장을 바로 찾아드려요.',
  },
];

/** 3페이지: 서비스 핵심 가치 3가지. */
export function ValueSection() {
  return (
    <section className="bg-surface py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="text-center">
          <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">왜 보장체크인가요?</h2>
          <p className="mt-3 text-sm text-muted sm:text-base">
            믿을 수 있는 근거와 함께, 놓친 보장을 정확하게 찾아드립니다.
          </p>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          {VALUES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="flex flex-col gap-3 rounded-card bg-canvas/60 p-6 ring-1 ring-line"
            >
              <span className="flex size-11 items-center justify-center rounded-xl bg-primary-tint text-primary">
                <Icon className="size-5" />
              </span>
              <h3 className="text-lg font-bold text-ink">{title}</h3>
              <p className="text-sm leading-6 text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 커밋 보류**

3페이지 그룹. **커밋하지 않고** Task 9 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 8: LandingFooter

**Files:**
- Create: `frontend/src/features/landing/components/LandingFooter.tsx`

- [ ] **Step 1: 컴포넌트 작성**

`frontend/src/features/landing/components/LandingFooter.tsx`:

```tsx
import { ShieldCheck } from 'lucide-react';

const LINKS = ['서비스 소개', '이용약관', '개인정보처리방침', '고객센터'];

/** 랜딩 하단 footer (정적). */
export function LandingFooter() {
  return (
    <footer className="border-t border-line bg-canvas">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-10 sm:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-primary">
            <ShieldCheck className="size-5" />
            <span className="text-base font-bold text-ink">보장체크</span>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2">
            {LINKS.map(label => (
              <button
                key={label}
                type="button"
                className="text-sm text-muted transition-colors hover:text-ink"
              >
                {label}
              </button>
            ))}
          </nav>
        </div>

        <p className="text-xs leading-5 text-muted">
          ※ 본 서비스의 분석 결과는 참고용이며, 실제 보장 여부는 약관 및 개별 상황에 따라 달라질 수
          있습니다.
        </p>
        <p className="text-xs text-muted">© 2026 보장체크. All rights reserved.</p>
      </div>
    </footer>
  );
}
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 커밋 보류**

3페이지 그룹. **커밋하지 않고** Task 9 끝의 페이지 단위 커밋에서 함께 올린다.

---

## Task 9: LandingPage 최종 조립

플레이스홀더를 실제 섹션 조립으로 교체한다.

**Files:**
- Modify: `frontend/src/pages/LandingPage.tsx`

- [ ] **Step 1: LandingPage 교체**

`frontend/src/pages/LandingPage.tsx` 전체를 다음으로 교체:

```tsx
import { AppHeader } from '@/components/common/AppHeader';
import { HeroSection } from '@/features/landing/components/HeroSection';
import { ScenarioSection } from '@/features/landing/components/ScenarioSection';
import { ValueSection } from '@/features/landing/components/ValueSection';
import { LandingFooter } from '@/features/landing/components/LandingFooter';

/** 서비스 소개 랜딩페이지 (루트 진입점). */
export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <AppHeader />
      <main className="flex-1">
        <HeroSection />
        <ScenarioSection />
        <ValueSection />
      </main>
      <LandingFooter />
    </div>
  );
}

export default LandingPage;
```

- [ ] **Step 2: 빌드/린트 검증**

Run: `pnpm lint && pnpm build`
Expected: 통과.

- [ ] **Step 3: 수동 전체 확인**

`pnpm dev` 후 `http://localhost:5173/`에서:
- 히어로 제목 둘째 줄이 3개 문구로 순환
- 우측 미니 UI가 홈(타자기)→상황 확인→분석 결과로 순환
- CTA 2개 클릭 시 `/home`으로 이동
- 시나리오 카드가 좌측으로 무한 스크롤, hover 시 멈춤
- 핵심 가치 3카드, footer 표시
- 모바일 폭에서 1열로 정렬
- OS의 "동작 줄이기(reduce motion)" 설정 시 애니메이션 정지
Expected: 모두 정상.

- [ ] **Step 4: 3페이지 커밋 (Task 7·8·9 일괄)**

3페이지(핵심 가치 + footer + 최종 조립) 작업을 한 번에 커밋한다.

```bash
git add frontend/src/features/landing/components/ValueSection.tsx \
  frontend/src/features/landing/components/LandingFooter.tsx \
  frontend/src/pages/LandingPage.tsx
git commit -m "feat(frontend): 핵심 가치·footer 섹션 추가 및 랜딩페이지 완성"
```

---

## Self-Review 결과

**Spec coverage:**
- 라우팅(`/`=랜딩, `/home`=홈, CTA→`/home`) → Task 1 ✓
- 색상 토큰만 사용 → 전 컴포넌트가 기존 토큰 클래스 사용 ✓
- 히어로(AppHeader·배지·로테이트 제목·CTA 2개·미니 UI) → Task 3,4,5,9 ✓
- 시나리오 마퀴(무한·hover 정지·데이터 분리) → Task 2,6 ✓
- 핵심 가치 3카드 → Task 7 ✓
- footer → Task 8 ✓
- 반응형·reduce-motion → 각 컴포넌트 + Task 9 수동 확인 ✓
- 범위 밖(최종 CTA 배너/FAQ/이용단계 요약) → 미포함 ✓

**Placeholder scan:** 모든 코드 스텝에 실제 코드 포함, TBD/TODO 없음 ✓

**Type consistency:** `Scenario`(id·question·tag)는 Task 2 정의를 Task 6에서 그대로 사용. `RotatingHeadline`/`HeroFlowAnimation` props(`className`)는 Task 5에서 일치하게 호출. `LandingPage`/`HeroSection` 등 export 이름 일관 ✓
