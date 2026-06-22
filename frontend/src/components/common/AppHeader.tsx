import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import { UserMenu } from '@/components/common/UserMenu';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { label: '홈', active: true },
  { label: '분석 내역', active: false },
  { label: '보험 관리', active: false },
  { label: '고객센터', active: false },
];

/** 상단 글로벌 헤더 (로고 · 내비게이션 · 사용자 영역). */
export function AppHeader() {
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

        <UserMenu />
      </div>
    </header>
  );
}
