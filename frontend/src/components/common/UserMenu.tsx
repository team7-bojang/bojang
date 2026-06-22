import { User } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useAuthSession } from '@/features/auth/hooks/useAuthSession';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';

/** 헤더 우측 사용자 영역. 세션 유무에 따라 로그인 버튼 / 사용자 이름 표시. */
export function UserMenu() {
  const { user, loading } = useAuthSession();
  const openAuth = useAuthModalStore(state => state.openAuth);

  if (loading) {
    return null;
  }

  if (!user) {
    return (
      <Button type="button" size="sm" onClick={() => openAuth('login')}>
        로그인
      </Button>
    );
  }

  const name = (user.user_metadata?.name as string | undefined) ?? user.email ?? '사용자';

  return (
    <div className="flex items-center gap-2 rounded-full px-2 py-1.5">
      <span className="flex size-8 items-center justify-center rounded-full bg-primary-tint text-primary">
        <User className="size-4" />
      </span>
      <span className="text-sm font-semibold text-ink">{name}</span>
    </div>
  );
}
