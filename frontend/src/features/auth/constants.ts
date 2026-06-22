import type { AuthCopy, AuthMode } from './types';

export const AUTH_COPY: Record<AuthMode, AuthCopy> = {
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
};
