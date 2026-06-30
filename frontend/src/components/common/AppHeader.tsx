import { Link } from 'react-router-dom';

import { UserMenu } from '@/components/common/UserMenu';

/** 상단 글로벌 헤더 (로고 · 내비게이션 · 사용자 영역). */
export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2 text-primary">
          <span className="font-logo text-2xl font-extrabold text-ink">보장zip</span>
        </Link>

        <UserMenu />
      </div>
    </header>
  );
}
