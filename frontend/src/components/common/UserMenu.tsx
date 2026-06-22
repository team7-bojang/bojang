import { ChevronDown, LogOut, User } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { useAuthSession } from '@/features/auth/hooks/useAuthSession';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';
import { supabase } from '@/lib/supabase';

/** 헤더 우측 사용자 영역. 세션 유무에 따라 로그인 버튼 / 사용자 메뉴(로그아웃) 표시. */
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
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-full px-2 py-1.5 transition-colors hover:bg-canvas"
        >
          <span className="flex size-8 items-center justify-center rounded-full bg-primary-tint text-primary">
            <User className="size-4" />
          </span>
          <span className="text-sm font-semibold text-ink">{name}</span>
          <ChevronDown className="size-4 text-muted" />
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-40 p-1">
        <button
          type="button"
          onClick={() => supabase.auth.signOut()}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-ink transition-colors hover:bg-canvas"
        >
          <LogOut className="size-4 text-muted" />
          로그아웃
        </button>
      </PopoverContent>
    </Popover>
  );
}
