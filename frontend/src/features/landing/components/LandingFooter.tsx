import { ShieldCheck } from 'lucide-react';

const LINKS = [
  { label: '서비스 소개', href: '#hero' },
  { label: '고객센터', href: '/analyze' },
];

/** 랜딩 하단 footer (정적). */
export function LandingFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-10 sm:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-primary">
            <ShieldCheck className="size-5" />
            <span className="font-logo text-lg font-extrabold text-ink">보장zip</span>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2">
            {LINKS.map(({ label, href }) => (
              <a
                key={label}
                href={href}
                className="text-sm text-muted transition-colors hover:text-ink"
              >
                {label}
              </a>
            ))}
          </nav>
        </div>

        <p className="text-xs leading-5 text-muted">
          ※ 본 서비스의 분석 결과는 참고용이며, 실제 보장 여부는 약관 및 개별 상황에 따라 달라질 수
          있습니다.
        </p>
        <p className="text-xs text-muted">© 2026 보장zip. All rights reserved.</p>
      </div>
    </footer>
  );
}
