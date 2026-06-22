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
