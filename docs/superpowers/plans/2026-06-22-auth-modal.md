# 로그인/회원가입 모달 전환 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/login`·`/signup` 풀페이지 인증 화면을 전역 store로 구동되는 오버레이 모달로 전환한다.

**Architecture:** zustand store(`authModalStore`)가 모달 open/mode/message 상태를 보유한다. `App.tsx` 루트에 마운트된 `AuthModal`(Radix Dialog)이 store를 구독해 기존 `AuthForm`을 렌더한다. `AppHeader`의 "로그인" 버튼이 `openAuth('login')`로 트리거한다. 라우트(`/login`, `/signup`)와 `AuthPage`·`AuthHero`·`AuthHeader`는 제거한다.

**Tech Stack:** React 19, react-router-dom 7, zustand 5, react-hook-form 7 + zod 4, `@radix-ui/react-dialog`(신규), Tailwind 4.

> **검증 노트:** frontend에는 단위 테스트 러너가 없다. 각 태스크 검증은 `pnpm --dir frontend build`(= `tsc -b && vite build`, 타입체크 포함)와 `pnpm --dir frontend lint`로 한다. 명령은 저장소 루트(`C:\Users\sara0\Project\bojang`)에서 실행한다. 커밋 스코프는 `frontend`.

---

### Task 1: `@radix-ui/react-dialog` 의존성 추가

**Files:**
- Modify: `frontend/package.json` (dependencies)
- Modify: `frontend/pnpm-lock.yaml`

- [ ] **Step 1: 의존성 설치**

Run: `pnpm --dir frontend add @radix-ui/react-dialog`
Expected: `dependencies: + @radix-ui/react-dialog`, `pnpm-lock.yaml` 갱신.

- [ ] **Step 2: 설치 확인**

Run: `pnpm --dir frontend list @radix-ui/react-dialog`
Expected: 버전이 출력됨 (예: `@radix-ui/react-dialog 1.x`).

- [ ] **Step 3: 커밋**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml
git commit -m "chore(frontend): 모달용 @radix-ui/react-dialog 추가"
```

---

### Task 2: `authModalStore` 작성

기존 store 패턴은 `frontend/src/features/case/store/caseStore.ts` 를 따른다 (`create<State>()(set => ({...}))`).

**Files:**
- Create: `frontend/src/features/auth/store/authModalStore.ts`

- [ ] **Step 1: store 작성**

```ts
import { create } from 'zustand';

import type { AuthMode } from '@/features/auth/types';

interface AuthModalState {
  isOpen: boolean;
  mode: AuthMode;
  message: string | null;
  openAuth: (mode?: AuthMode) => void;
  setMode: (mode: AuthMode) => void;
  switchToLoginWithMessage: (message: string) => void;
  close: () => void;
}

export const useAuthModalStore = create<AuthModalState>(set => ({
  isOpen: false,
  mode: 'login',
  message: null,
  openAuth: (mode = 'login') => set({ isOpen: true, mode, message: null }),
  setMode: mode => set({ mode, message: null }),
  switchToLoginWithMessage: message => set({ mode: 'login', message }),
  close: () => set({ isOpen: false, message: null }),
}));
```

- [ ] **Step 2: 타입체크**

Run: `pnpm --dir frontend build`
Expected: PASS (에러 없음).

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/features/auth/store/authModalStore.ts
git commit -m "feat(frontend): 인증 모달 상태 store 추가"
```

---

### Task 3: `AUTH_COPY` 에 `heroHeadline` 추가 / `switchTo` 제거

**Files:**
- Modify: `frontend/src/features/auth/types.ts` (`AuthCopy`)
- Modify: `frontend/src/features/auth/constants.ts` (`AUTH_COPY`)

- [ ] **Step 1: `AuthCopy` 타입 수정**

`frontend/src/features/auth/types.ts` 의 `AuthCopy` 인터페이스에서 `switchTo` 를 제거하고 선택 필드 `heroHeadline` 을 추가한다. 전체 파일은 다음과 같이 된다:

```ts
export type AuthMode = 'login' | 'signup';

export interface AuthCopy {
  title: string;
  description: string;
  submit: string;
  switchText: string;
  switchLabel: string;
  /** 회원가입 모달 상단에 노출하는 마케팅 헤드라인. 로그인은 미설정. */
  heroHeadline?: string;
}
```

- [ ] **Step 2: `AUTH_COPY` 수정**

`frontend/src/features/auth/constants.ts` 전체를 다음으로 교체한다 (`switchTo` 제거, signup 에 `heroHeadline` 추가):

```ts
import type { AuthCopy, AuthMode } from './types';

export const AUTH_COPY = {
  login: {
    title: '다시 오신 걸 환영합니다',
    description: '저장된 보험 정보와 분석 내역을 이어서 확인하세요.',
    submit: '로그인',
    switchText: '아직 계정이 없으신가요?',
    switchLabel: '회원가입',
  },
  signup: {
    title: '보장체크 시작하기',
    description: '가입한 보험과 진료 상황을 안전하게 관리해 보세요.',
    submit: '회원가입',
    switchText: '이미 계정이 있으신가요?',
    switchLabel: '로그인',
    heroHeadline: '보험금 청구 가능성을\n놓치지 않게 확인하세요',
  },
} satisfies Record<AuthMode, AuthCopy>;
```

- [ ] **Step 3: 타입체크**

Run: `pnpm --dir frontend build`
Expected: FAIL — `AuthForm.tsx` 가 아직 `copy.switchTo` 를 참조하므로 타입 에러. (Task 4에서 해소) 빌드 에러 메시지에 `switchTo` 가 보이면 정상.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/features/auth/types.ts frontend/src/features/auth/constants.ts
git commit -m "feat(frontend): AUTH_COPY에 heroHeadline 추가, switchTo 제거"
```

> 참고: 이 시점에 빌드는 일시적으로 깨진다. Task 4에서 `AuthForm` 을 고치면 복구된다. (TDD의 "실패 → 통과" 흐름과 동일하게, Task 3+4를 연속 실행한다.)

---

### Task 4: `AuthForm` 을 store 기반으로 수정

기존 zod + react-hook-form 검증 로직은 유지하고, 모드 전환·성공 처리를 store 연결로 바꾼다.

**Files:**
- Modify: `frontend/src/features/auth/components/AuthForm.tsx`

- [ ] **Step 1: `AuthForm` 전체 교체**

`frontend/src/features/auth/components/AuthForm.tsx` 전체를 다음으로 교체한다. 변경 핵심: `react-router-dom`의 `Link` 제거, props 콜백 제거 후 store 구독, 모드 전환 링크 → 버튼(`setMode`), 회원가입 성공 → `switchToLoginWithMessage`, 로그인 성공 → `close`, 회원가입 모드에 `heroHeadline` 노출, `message`는 store에서 주입.

```tsx
import { useState } from 'react';
import { useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AUTH_COPY } from '@/features/auth/constants';
import { getAuthSchema, type AuthFormValues } from '@/features/auth/schema';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';
import { getAuthErrorMessage } from '@/features/auth/utils/authError';
import { supabase } from '@/lib/supabase';

export function AuthForm() {
  const mode = useAuthModalStore(state => state.mode);
  const storeMessage = useAuthModalStore(state => state.message);
  const setMode = useAuthModalStore(state => state.setMode);
  const switchToLoginWithMessage = useAuthModalStore(state => state.switchToLoginWithMessage);
  const close = useAuthModalStore(state => state.close);

  const copy = AUTH_COPY[mode];
  const isSignup = mode === 'signup';

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AuthFormValues>({
    resolver: zodResolver(getAuthSchema(mode)) as unknown as Resolver<AuthFormValues>,
    mode: 'onTouched',
    defaultValues: { name: '', email: '', password: '' },
  });

  const onSubmit = handleSubmit(async values => {
    setError(null);

    const { error: authError } = isSignup
      ? await supabase.auth.signUp({
          email: values.email,
          password: values.password,
          options: {
            data: {
              name: values.name,
            },
          },
        })
      : await supabase.auth.signInWithPassword({
          email: values.email,
          password: values.password,
        });

    if (authError) {
      setError(getAuthErrorMessage(authError.message));
      return;
    }

    if (isSignup) {
      await supabase.auth.signOut();
      switchToLoginWithMessage(
        '회원가입이 완료되었습니다. 가입한 이메일과 비밀번호로 로그인해 주세요.'
      );
      return;
    }

    close();
  });

  return (
    <div>
      <div className="text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-primary text-white">
          {isSignup ? <UserRound className="size-6" /> : <LockKeyhole className="size-6" />}
        </div>
        {isSignup && copy.heroHeadline && (
          <p className="mt-4 whitespace-pre-line text-xl font-black leading-7 text-ink">
            {copy.heroHeadline}
          </p>
        )}
        <h2 className="mt-2 text-2xl font-black text-ink">{copy.title}</h2>
        <p className="mt-2 text-sm leading-6 text-muted">{copy.description}</p>
      </div>

      <form className="mt-7 space-y-4" onSubmit={onSubmit} noValidate>
        {isSignup && (
          <label className="block">
            <span className="text-sm font-bold text-ink">이름</span>
            <Input
              className="mt-2"
              placeholder="김보장"
              autoComplete="name"
              aria-invalid={Boolean(errors.name)}
              {...register('name')}
            />
            {errors.name && (
              <span className="mt-1.5 block text-sm font-medium text-red-600">
                {errors.name.message}
              </span>
            )}
          </label>
        )}

        <label className="block">
          <span className="text-sm font-bold text-ink">이메일</span>
          <div className="relative mt-2">
            <Mail className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted" />
            <Input
              className="pl-11"
              type="email"
              placeholder="name@example.com"
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              {...register('email')}
            />
          </div>
          {errors.email && (
            <span className="mt-1.5 block text-sm font-medium text-red-600">
              {errors.email.message}
            </span>
          )}
        </label>

        <label className="block">
          <span className="text-sm font-bold text-ink">비밀번호</span>
          <div className="relative mt-2">
            <LockKeyhole className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted" />
            <Input
              className="px-11"
              type={showPassword ? 'text' : 'password'}
              placeholder="6자 이상 입력"
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              aria-invalid={Boolean(errors.password)}
              {...register('password')}
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-muted transition-colors hover:bg-canvas hover:text-ink"
              onClick={() => setShowPassword(prev => !prev)}
              aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          {errors.password && (
            <span className="mt-1.5 block text-sm font-medium text-red-600">
              {errors.password.message}
            </span>
          )}
        </label>

        {error && (
          <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700 ring-1 ring-red-100">
            {error}
          </p>
        )}
        {storeMessage && (
          <p className="rounded-xl bg-primary-tint px-4 py-3 text-sm font-medium text-primary ring-1 ring-primary/10">
            {storeMessage}
          </p>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? '처리 중...' : copy.submit}
          {!isSubmitting && <ArrowRight />}
        </Button>
      </form>

      <div className="mt-6 flex items-center justify-center gap-2 text-sm text-muted">
        <span>{copy.switchText}</span>
        <button
          type="button"
          onClick={() => setMode(isSignup ? 'login' : 'signup')}
          className="font-bold text-primary hover:text-primary/80"
        >
          {copy.switchLabel}
        </button>
      </div>
    </div>
  );
}
```

> 주의: `<section>` 래퍼(배경·ring·padding)는 제거했다 — 그 스타일은 Task 5의 Dialog `Content` 가 담당한다. `AuthForm` 은 모달 내부 콘텐츠만 책임진다.

- [ ] **Step 2: 타입체크**

Run: `pnpm --dir frontend build`
Expected: FAIL — `AuthPage.tsx` 가 아직 옛 `AuthForm` props(`mode`, `onLoginSuccess` 등)를 넘기므로 에러. (Task 6에서 `AuthPage` 삭제 시 해소) `AuthForm.tsx` 자체의 `switchTo` 에러는 사라져야 한다.

- [ ] **Step 3: lint**

Run: `pnpm --dir frontend lint`
Expected: `AuthForm.tsx` 관련 신규 에러 없음.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/features/auth/components/AuthForm.tsx
git commit -m "feat(frontend): AuthForm을 모달 store 기반으로 전환"
```

---

### Task 5: `AuthModal` 컴포넌트 작성

**Files:**
- Create: `frontend/src/features/auth/components/AuthModal.tsx`

- [ ] **Step 1: `AuthModal` 작성**

`@radix-ui/react-dialog` 로 `AuthForm` 을 감싼다. `open`/`onOpenChange` 를 store에 연결하면 ESC·바깥 클릭이 자동으로 `close` 를 호출한다. a11y용 `Title`/`Description` 은 시각적으로는 폼 안에서 보여주므로 Radix `VisuallyHidden` 대신 `sr-only` 클래스로 숨긴 노드를 둔다.

```tsx
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import { AUTH_COPY } from '@/features/auth/constants';
import { AuthForm } from '@/features/auth/components/AuthForm';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';

export function AuthModal() {
  const isOpen = useAuthModalStore(state => state.isOpen);
  const mode = useAuthModalStore(state => state.mode);
  const close = useAuthModalStore(state => state.close);

  const copy = AUTH_COPY[mode];

  return (
    <Dialog.Root open={isOpen} onOpenChange={open => (open ? undefined : close())}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-card bg-surface p-6 shadow-xl ring-1 ring-line focus:outline-none sm:p-7">
          <Dialog.Title className="sr-only">{copy.title}</Dialog.Title>
          <Dialog.Description className="sr-only">{copy.description}</Dialog.Description>
          <Dialog.Close
            className="absolute right-4 top-4 flex size-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-canvas hover:text-ink"
            aria-label="닫기"
          >
            <X className="size-4" />
          </Dialog.Close>
          <AuthForm key={mode} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

> `key={mode}` 로 모드 전환 시 `AuthForm`(react-hook-form 상태 포함)이 리셋된다.

- [ ] **Step 2: 타입체크**

Run: `pnpm --dir frontend build`
Expected: 여전히 FAIL (Task 6 전까지 `AuthPage.tsx`/라우트 에러 잔존). `AuthModal.tsx` 자체 에러는 없어야 한다.

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/features/auth/components/AuthModal.tsx
git commit -m "feat(frontend): Radix Dialog 기반 AuthModal 추가"
```

---

### Task 6: 라우트 제거 · `AuthModal` 마운트 · 미사용 파일 삭제

**Files:**
- Modify: `frontend/src/App.tsx`
- Delete: `frontend/src/pages/AuthPage.tsx`
- Delete: `frontend/src/features/auth/components/AuthHero.tsx`
- Delete: `frontend/src/features/auth/components/AuthHeader.tsx`

- [ ] **Step 1: `App.tsx` 교체**

`/login`·`/signup` 라우트와 `AuthPage` import 를 제거하고, 라우터 안에 `AuthModal` 을 한 번 마운트한다. 전체를 다음으로 교체한다:

```tsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AuthModal } from '@/features/auth/components/AuthModal';
import { HomePage } from '@/pages/HomePage';
import { ConfirmPage } from '@/pages/ConfirmPage';
import { ResultPage } from '@/pages/ResultPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cases/:caseId/confirm" element={<ConfirmPage />} />
        <Route path="/cases/:caseId/result" element={<ResultPage />} />
      </Routes>
      <AuthModal />
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 2: 미사용 파일 삭제**

Run:
```bash
git rm frontend/src/pages/AuthPage.tsx frontend/src/features/auth/components/AuthHero.tsx frontend/src/features/auth/components/AuthHeader.tsx
```
Expected: 3개 파일 삭제됨.

- [ ] **Step 3: 잔존 참조 확인**

Run: `git -C C:\Users\sara0\Project\bojang grep -nE "AuthPage|AuthHero|AuthHeader" -- frontend/src`
Expected: 출력 없음 (어디서도 참조하지 않음).

- [ ] **Step 4: 타입체크 + lint**

Run: `pnpm --dir frontend build`
Expected: PASS (이제 빌드 복구).
Run: `pnpm --dir frontend lint`
Expected: 신규 에러 없음.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): 인증 라우트 제거하고 AuthModal 마운트, 미사용 페이지 삭제"
```

---

### Task 7: `AppHeader` 에 로그인 트리거 연결

`AppHeader` 의 하드코딩 사용자 영역을 "로그인" 버튼으로 교체한다.

**Files:**
- Modify: `frontend/src/features/home/components/AppHeader.tsx`

- [ ] **Step 1: `AppHeader` 수정**

`User`·`ChevronDown` 아이콘과 `userName` props 를 제거하고, 우측에 "로그인" 버튼을 둔다. 전체를 다음으로 교체한다:

```tsx
import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { label: '홈', active: true },
  { label: '분석 내역', active: false },
  { label: '보험 관리', active: false },
  { label: '고객센터', active: false },
];

/** 상단 글로벌 헤더 (로고 · 내비게이션 · 로그인). */
export function AppHeader() {
  const openAuth = useAuthModalStore(state => state.openAuth);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2 text-primary">
          <ShieldCheck className="size-6" />
          <span className="text-lg font-bold text-ink">보장체크</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(item => (
            <button
              key={item.label}
              type="button"
              className={cn(
                'relative rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                item.active ? 'text-primary' : 'text-muted hover:text-ink'
              )}
            >
              {item.label}
              {item.active && (
                <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-primary" />
              )}
            </button>
          ))}
        </nav>

        <Button type="button" size="sm" onClick={() => openAuth('login')}>
          로그인
        </Button>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: 잔존 참조 확인**

`AppHeader` 를 `userName` props 와 함께 쓰는 곳이 없는지 확인한다.
Run: `git -C C:\Users\sara0\Project\bojang grep -n "AppHeader" -- frontend/src`
Expected: `HomePage.tsx` 의 import 와 `<AppHeader />`(props 없음) 사용만 보인다. props 를 넘기는 곳이 있으면 제거한다.

- [ ] **Step 3: 타입체크 + lint**

Run: `pnpm --dir frontend build`
Expected: PASS.
Run: `pnpm --dir frontend lint`
Expected: 신규 에러 없음.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/features/home/components/AppHeader.tsx
git commit -m "feat(frontend): 헤더 로그인 버튼으로 인증 모달 트리거"
```

---

### Task 8: 최종 검증

**Files:** (없음 — 검증만)

- [ ] **Step 1: 전체 빌드**

Run: `pnpm --dir frontend build`
Expected: PASS.

- [ ] **Step 2: 전체 lint**

Run: `pnpm --dir frontend lint`
Expected: 기존 경고(`button.tsx` react-refresh) 외 신규 에러·경고 없음.

- [ ] **Step 3: 수동 확인 (`pnpm --dir frontend dev`)**

브라우저(http://localhost:5173)에서 확인:
- 헤더 "로그인" 클릭 → 모달 오픈
- 로그인 모드: 빈 값/잘못된 이메일/짧은 비밀번호 → 필드별 에러 노출
- "회원가입" 링크 클릭 → 회원가입 모드 전환(폼 리셋), 상단에 헤드라인 "보험금 청구 가능성을 / 놓치지 않게 확인하세요" 노출
- 회원가입 성공 → 로그인 모드로 전환 + 안내 메시지 표시
- ESC·바깥 클릭·X 버튼으로 모달 닫힘
```
