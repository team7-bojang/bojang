import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import type { CoverageAmountInput } from '@/features/case/queries';

export interface CoverageRow {
  riderId: string;
  rider: string;
  policy: string;
}

interface CoverageAmountFormProps {
  coverages: CoverageRow[];
  onApply: (amounts: CoverageAmountInput[]) => void;
  submitting: boolean;
}

const onlyDigits = (value: string) => value.replace(/[^0-9]/g, '');
const formatComma = (digits: string) => (digits ? Number(digits).toLocaleString('ko-KR') : '');

/** 분석으로 매칭된 보장에 보험증권 가입금액을 입력받아 예상 보험금을 재계산한다. */
export function CoverageAmountForm({ coverages, onApply, submitting }: CoverageAmountFormProps) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});

  const filledCount = useMemo(
    () => Object.values(values).filter(digits => Number(digits) > 0).length,
    [values]
  );

  if (coverages.length === 0) {
    return null;
  }

  const handleApply = () => {
    const amounts: CoverageAmountInput[] = coverages
      .map(coverage => ({
        rider_id: coverage.riderId,
        amount: Number(values[coverage.riderId] ?? ''),
        amount_source: '실증권',
      }))
      .filter(entry => entry.amount > 0);
    onApply(amounts);
  };

  return (
    <section className="mt-6 rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
      <button
        type="button"
        onClick={() => setOpen(prev => !prev)}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <span className="min-w-0">
          <span className="block text-lg font-black text-ink">
            가입금액을 입력하면 예상 보험금을 계산해드려요
          </span>
          <span className="mt-1 block text-sm font-medium text-muted">
            보험증권의 보장별 가입금액을 넣으면 실제 예상 금액이 표시됩니다 (선택)
          </span>
        </span>
        <span className="shrink-0 text-sm font-bold text-muted">{open ? '닫기 ▴' : '입력 ▾'}</span>
      </button>

      {open && (
        <div className="mt-5">
          <div className="divide-y divide-line/80">
            {coverages.map(coverage => {
              const digits = onlyDigits(values[coverage.riderId] ?? '');
              return (
                <label
                  key={coverage.riderId}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-bold text-ink">
                      {coverage.rider}
                    </span>
                    <span className="block truncate text-xs font-medium text-muted">
                      {coverage.policy}
                    </span>
                  </span>
                  <span className="flex items-center gap-1">
                    <input
                      inputMode="numeric"
                      value={formatComma(digits)}
                      onChange={event =>
                        setValues(prev => ({
                          ...prev,
                          [coverage.riderId]: onlyDigits(event.target.value),
                        }))
                      }
                      placeholder="0"
                      className="w-28 rounded-xl border border-line bg-canvas px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
                    />
                    <span className="text-sm font-medium text-muted">원</span>
                  </span>
                </label>
              );
            })}
          </div>
          <Button
            type="button"
            size="lg"
            className="mt-5 w-full"
            disabled={submitting || filledCount === 0}
            onClick={handleApply}
          >
            {submitting ? '계산 중…' : '예상 보험금 계산하기'}
          </Button>
        </div>
      )}
    </section>
  );
}
