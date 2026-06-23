import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { ChevronRight } from 'lucide-react';

import type { Benefit } from '../model';
import { formatWon } from '../utils/format';

export function BenefitRow({ benefit, onClick }: { benefit: Benefit; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:gap-5"
    >
      <InsurerLogo insurerId={benefit.insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{benefit.title}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">
          {benefit.insurerName} <span className="mx-2 text-line">|</span> {benefit.policyName}
        </span>
      </span>
      <span className="flex items-center gap-3">
        {'amount' in benefit ? (
          <span className="text-right text-xl font-black text-ink">
            {formatWon(benefit.amount)}원
          </span>
        ) : (
          <span className="text-right">
            <span className="block text-lg font-black text-red-600">{benefit.reason}</span>
            <span className="mt-1 hidden text-sm font-medium text-muted sm:block">
              조건: {benefit.condition}
            </span>
          </span>
        )}
        <ChevronRight className="size-5 shrink-0 text-muted" />
      </span>
    </button>
  );
}
