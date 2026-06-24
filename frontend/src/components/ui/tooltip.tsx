import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

interface TooltipProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export function Tooltip({ label, children, className }: TooltipProps) {
  return (
    <span className={cn('group relative inline-flex', className)} tabIndex={0}>
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-64 -translate-x-1/2 rounded-lg border border-line bg-ink px-3 py-2 text-xs font-medium leading-relaxed text-white shadow-lg group-hover:block group-focus:block">
        {label}
      </span>
    </span>
  );
}
