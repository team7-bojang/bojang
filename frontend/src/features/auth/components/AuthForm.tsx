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
