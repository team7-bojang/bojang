import { z } from 'zod';

import type { AuthMode } from './types';

/**
 * 인증 폼 검증 스키마.
 * - 로그인: 이메일 + 비밀번호
 * - 회원가입: 이름 + 이메일 + 비밀번호
 *
 * 이메일은 형식까지 검증하고, 메시지는 필드별로 노출한다.
 */
const emailField = z
  .string()
  .trim()
  .min(1, '이메일을 입력해 주세요.')
  .email('이메일 형식이 올바르지 않습니다.');

const passwordField = z.string().min(6, '비밀번호는 6자 이상 입력해 주세요.');

export const loginSchema = z.object({
  email: emailField,
  password: passwordField,
});

export const signupSchema = loginSchema.extend({
  name: z.string().trim().min(1, '이름을 입력해 주세요.'),
});

export type AuthFormValues = z.infer<typeof signupSchema>;

export function getAuthSchema(mode: AuthMode) {
  return mode === 'signup' ? signupSchema : loginSchema;
}
