# 로그인/회원가입 모달 전환 설계

> 작성일: 2026-06-22 · 범위: frontend

## 목표

현재 `/login` · `/signup` 풀페이지(`AuthPage`)로 동작하는 인증 화면을, 현재 화면 위에 뜨는 **오버레이 모달**로 전환한다. 페이지 이동 없이 어디서든 로그인/회원가입을 띄운다.

## 범위

- **포함**: 페이지 → 모달 표현 전환, 전역 store 기반 open 제어, 헤더 로그인 트리거, 기존 zod/RHF 폼 재사용
- **제외(YAGNI)**: 소셜 로그인(Google/SSO), 이메일→비밀번호 단계형 흐름, 로그인/비로그인 세션 분기 표시

## 결정 사항

| 항목 | 결정 |
| --- | --- |
| 여는 방식 | 전역 상태(zustand) 구동 — `/login` `/signup` 라우트 제거 |
| 모달 프리미티브 | `@radix-ui/react-dialog` 추가 (기존 Radix와 일관, a11y 무료) |
| 헤더 트리거 | `AppHeader`의 하드코딩 사용자 영역을 "로그인" 버튼으로 교체 |
| 폼 로직 | 기존 zod 스키마 + react-hook-form 그대로 재사용 |

## 컴포넌트 / 데이터 흐름

```
AppHeader '로그인' 버튼 ──openAuth('login')──▶ authModalStore
                                                   │ (isOpen, mode, message)
App.tsx 루트의 <AuthModal /> ◀──구독────────────────┘
   └─ Radix Dialog
        └─ AuthForm (mode, message)
             ├─ 모드 전환 버튼 ──setMode('signup'|'login')──▶ store
             ├─ 회원가입 성공 ──setMode('login') + 안내 메시지──▶ store (모달 유지)
             └─ 로그인 성공 ──close()──▶ store
```

### 1. `features/auth/store/authModalStore.ts` (신규)

zustand store.

```ts
interface AuthModalState {
  isOpen: boolean;
  mode: AuthMode;
  message: string | null;
  openAuth: (mode?: AuthMode) => void;            // 기본 'login'
  setMode: (mode: AuthMode) => void;              // message 초기화
  switchToLoginWithMessage: (message: string) => void; // 회원가입 성공 핸드오프
  close: () => void;                              // isOpen=false, message=null
}
```

- `openAuth(mode)`: `isOpen=true`, `mode` 설정, `message=null`
- `setMode(mode)`: 모드 전환 (메시지 유지가 필요한 회원가입→로그인은 별도 처리)
- 회원가입 성공 시: `mode='login'`로 바꾸면서 안내 `message` 세팅 (한 액션으로 처리하는 `switchToLoginWithMessage(message)` 제공)
- `close()`: 닫고 `message` 정리

### 2. `features/auth/components/AuthModal.tsx` (신규)

- `@radix-ui/react-dialog` 의 `Root`/`Portal`/`Overlay`/`Content`로 구성
- `open`은 store의 `isOpen`, `onOpenChange`(false)는 store `close()` 연결 → ESC·바깥 클릭 닫기 자동
- 내부에 `AuthForm` 렌더 (`key={mode}` 로 모드 전환 시 폼 리셋)
- 컴팩트 카드 레이아웃. **Hero(마케팅 패널)는 모달에서 제외** — `AUTH_COPY`의 title/description이 모달 헤더 역할
- Dialog `Title`/`Description`로 a11y 라벨 제공 (`AUTH_COPY` 재사용)

### 3. `features/auth/components/AuthForm.tsx` (수정)

기존 zod + RHF 검증 로직은 **그대로 유지**. 인터페이스만 모달에 맞게 조정:

- 로그인↔회원가입 전환: `<Link to={switchTo}>` → `<button onClick={() => setMode(...)}>` (페이지 이동 제거)
- `onLoginSuccess` 기본 동작을 store `close()` 로 변경. `AuthModal`이 성공 핸들러로 `close`를 주입하고, 기존 `navigate('/')` 는 제거
- `onSignupSuccess` → store `switchToLoginWithMessage(...)` 로 대체 (모달 안에서 로그인 모드 + 안내 메시지)
- `initialMessage`/`message`는 store의 `message`에서 주입

> 회원가입 성공 후 안내 문구는 기존과 동일: "회원가입이 완료되었습니다. 가입한 이메일과 비밀번호로 로그인해 주세요."

### 4. `features/home/components/AppHeader.tsx` (수정)

- 하드코딩된 사용자 버튼(`김보장님`)을 "로그인" 버튼으로 교체, `onClick={() => openAuth('login')}`
- (세션 분기는 범위 밖 — 추후 별도 작업)

### 5. 라우팅 / 정리

- `App.tsx`: `/login` `/signup` 라우트 제거. 루트에 `<AuthModal />` 1회 마운트
- 삭제: `pages/AuthPage.tsx`, `features/auth/components/AuthHero.tsx`, `features/auth/components/AuthHeader.tsx` (서로만 참조, 외부 의존 없음)
- `features/auth/constants.ts`: `AUTH_COPY`의 `switchTo`(경로) 필드 제거, `AuthCopy` 타입에서도 제거. `switchLabel`/`switchText`는 모드 전환 버튼용으로 유지
- (선택) `/login` 직접 진입 대비 catch 처리는 이번 범위 밖 — 필요 시 추후

## 의존성

- `@radix-ui/react-dialog` 추가 → `pnpm-lock.yaml` 함께 커밋, PR 본문에 사유 명시 (CONTRIBUTING 9)

## 에러 / 엣지 케이스

- 서버 인증 에러: 기존 `getAuthErrorMessage` 그대로, 모달 폼 내부에 표시
- 모드 전환 시 폼 값·검증 상태 초기화(`key={mode}`)
- 회원가입 성공 후 즉시 `signOut()` 하는 기존 동작 유지 (이메일 인증 전 자동 로그인 방지)
- 모달 열림 중 스크롤 잠금·포커스 트랩은 Radix Dialog가 처리

## 테스트 / 확인

- 로그인 모드: 빈 값·잘못된 이메일·짧은 비밀번호에서 필드별 에러 노출
- 회원가입 모드: 이름 필수 검증, 성공 시 로그인 모드로 전환 + 안내 메시지
- 헤더 "로그인" 클릭 → 모달 오픈, ESC·바깥 클릭·X로 닫힘
- 모드 전환 버튼으로 로그인↔회원가입 전환 시 폼 리셋
- `pnpm lint` · `pnpm build`(타입체크) 통과
```
