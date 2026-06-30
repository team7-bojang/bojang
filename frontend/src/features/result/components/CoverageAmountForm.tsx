import { ChevronUp } from 'lucide-react';
import { useLayoutEffect, useMemo, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { type InsurerId } from '@/features/insurance/data/insurers';
import { cn } from '@/lib/utils';

import type { MedicalCostInput } from '../model';
import { formatWon } from '../utils/format';

export interface CoverageGroupRow {
  key: string;
  policy: string;
  insurerId: InsurerId;
  kind: 'daily' | 'fixed';
  riders: string[];
}

interface CoverageAmountFormProps {
  groups: CoverageGroupRow[];
  initialAmounts: Record<string, number>;
  expectedAmount: number | null;
  hasReimbursementRiders: boolean;
  initialMedicalCosts: MedicalCostInput;
  submitting: boolean;
  onApply: (amounts: Record<string, number>, costs: MedicalCostInput) => void;
  onMeasure?: (height: number) => void;
}

const onlyDigits = (value: string) => value.replace(/[^0-9]/g, '');
const formatComma = (digits: string) => (digits ? Number(digits).toLocaleString('ko-KR') : '');
const toInputDigits = (value: number | undefined) => (value !== undefined ? String(value) : '');

const createInitialValues = (groups: CoverageGroupRow[], initialAmounts: Record<string, number>) =>
  Object.fromEntries(
    groups.map(group => [
      group.key,
      initialAmounts[group.key] ? String(initialAmounts[group.key]) : '',
    ])
  );

export function CoverageAmountForm({
  groups,
  initialAmounts,
  expectedAmount,
  hasReimbursementRiders,
  initialMedicalCosts,
  submitting,
  onApply,
  onMeasure,
}: CoverageAmountFormProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  const [open, setOpen] = useState(false);

  const [values, setValues] = useState<Record<string, string>>(() =>
    createInitialValues(groups, initialAmounts)
  );

  const [patientPaid, setPatientPaid] = useState(() =>
    toInputDigits(initialMedicalCosts.patient_paid_amount)
  );

  const [nonCovered, setNonCovered] = useState(() =>
    toInputDigits(initialMedicalCosts.non_covered_amount)
  );

  useLayoutEffect(() => {
    if (!onMeasure) {
      return;
    }

    if (groups.length === 0 && !hasReimbursementRiders) {
      onMeasure(0);
      return;
    }

    const el = panelRef.current;
    if (!el) {
      return;
    }

    const update = () => onMeasure(el.offsetHeight);

    update();

    const observer = new ResizeObserver(update);
    observer.observe(el);

    return () => observer.disconnect();
  }, [onMeasure, groups.length, hasReimbursementRiders]);

  const filledAmountCount = useMemo(
    () => Object.values(values).filter(digits => Number(digits) > 0).length,
    [values]
  );

  const hasMedicalCostInput = Number(patientPaid) > 0 || Number(nonCovered) > 0;

  if (groups.length === 0 && !hasReimbursementRiders) {
    return null;
  }

  const handleChange = (key: string, value: string) => {
    setValues(prev => ({ ...prev, [key]: onlyDigits(value) }));
  };

  const handleApply = () => {
    const amounts: Record<string, number> = {};

    for (const [key, digits] of Object.entries(values)) {
      const amount = Number(digits || 0);

      if (amount > 0) {
        amounts[key] = amount;
      }
    }

    onApply(amounts, {
      patient_paid_amount: patientPaid ? Number(patientPaid) : undefined,
      non_covered_amount: nonCovered ? Number(nonCovered) : undefined,
    });
  };

  const closeIfNotEditing = () => {
    const el = panelRef.current;

    if (el && el.contains(document.activeElement)) {
      return;
    }

    setOpen(false);
  };

  const hasAmount = expectedAmount !== null && expectedAmount > 0;

  const description = hasReimbursementRiders
    ? '가입금액, 본인부담금, 비급여 금액을 기준으로 보장 참고 금액을 계산해요.'
    : '가입금액을 기준으로 보장 참고 금액을 계산해요.';

  return (
    <div
      ref={panelRef}
      className="fixed inset-x-0 bottom-0 z-40 overflow-hidden rounded-t-[1.75rem] border border-b-0 border-line bg-surface shadow-[0_-8px_28px_rgba(11,18,32,0.10)]"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={closeIfNotEditing}
    >
      <div className="mx-auto flex max-h-[calc(100svh-5rem)] max-w-5xl flex-col px-5 py-3 sm:px-8">
        <button
          type="button"
          onClick={() => setOpen(prev => !prev)}
          className="flex w-full items-center justify-between gap-3 text-left"
          aria-expanded={open}
        >
          <span className="min-w-0">
            <span className="block text-md font-bold text-ink">
              {hasAmount ? '금액 수정하기' : '금액 정보를 입력해주세요'}
            </span>
            <span className="mt-0.5 block text-sm font-medium text-muted">{description}</span>
          </span>

          <span className="flex shrink-0 items-center gap-3">
            <span className="text-right">
              <span className="block text-sm font-semibold text-muted">예상 보험금</span>
              <span className="block text-lg font-extrabold text-primary">
                {hasAmount ? `${formatWon(expectedAmount)}원` : '입력 시 산출'}
              </span>
            </span>

            <ChevronUp
              className={cn('size-5 text-muted transition-transform', open && 'rotate-180')}
            />
          </span>
        </button>

        <div
          className={cn(
            'grid transition-[grid-template-rows] duration-300 ease-out',
            open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
          )}
        >
          <div
            className={cn(
              'min-h-0 overflow-hidden transition-opacity duration-300',
              open ? 'opacity-100' : 'opacity-0'
            )}
          >
            <div className="mt-3 max-h-[min(50svh,28rem)] space-y-2 overflow-y-auto overscroll-contain px-px pb-1 scrollbar-hide">
              {groups.map(row => {
                const isDaily = row.kind === 'daily';

                return (
                  <label
                    key={row.key}
                    className="flex items-center gap-3 rounded-xl border border-line bg-canvas/60 px-3 py-2 sm:px-4"
                  >
                    <InsurerLogo
                      insurerId={row.insurerId}
                      size="sm"
                      className="shrink-0 rounded-full"
                    />

                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5">
                        <span className="truncate text-sm font-bold text-ink">{row.policy}</span>

                        <span
                          className={cn(
                            'shrink-0 rounded-full px-1.5 py-0.5 text-[0.65rem] font-bold',
                            isDaily ? 'bg-primary-tint text-primary' : 'bg-canvas text-muted'
                          )}
                        >
                          {isDaily ? '특별약관 가입금액' : '가입금액'}
                        </span>
                      </span>

                      <span className="mt-0.5 block truncate text-xs font-medium text-muted">
                        {row.riders.join(', ')}
                      </span>
                    </span>

                    <span className="flex shrink-0 items-center gap-1">
                      <input
                        inputMode="numeric"
                        value={formatComma(values[row.key] ?? '')}
                        onChange={event => handleChange(row.key, event.target.value)}
                        placeholder="0"
                        className="w-24 rounded-xl border border-line bg-surface px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
                      />
                      <span className="text-sm font-medium text-muted">원</span>
                    </span>
                  </label>
                );
              })}

              {hasReimbursementRiders && (
                <>
                  <label className="flex items-center gap-3 rounded-xl border border-line bg-canvas/60 px-3 py-2 sm:px-4">
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5">
                        <span className="truncate text-sm font-bold text-ink">실손 본인부담금</span>
                        <span className="shrink-0 rounded-full bg-primary-tint px-1.5 py-0.5 text-[0.65rem] font-bold text-primary">
                          실손
                        </span>
                      </span>
                      <span className="mt-0.5 block truncate text-xs font-medium text-muted">
                        영수증의 급여 본인부담금
                      </span>
                    </span>

                    <span className="flex shrink-0 items-center gap-1">
                      <input
                        inputMode="numeric"
                        value={formatComma(patientPaid)}
                        onChange={event => setPatientPaid(onlyDigits(event.target.value))}
                        placeholder="0"
                        className="w-24 rounded-xl border border-line bg-surface px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
                      />
                      <span className="text-sm font-medium text-muted">원</span>
                    </span>
                  </label>

                  <label className="flex items-center gap-3 rounded-xl border border-line bg-canvas/60 px-3 py-2 sm:px-4">
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5">
                        <span className="truncate text-sm font-bold text-ink">비급여 금액</span>
                        <span className="shrink-0 rounded-full bg-primary-tint px-1.5 py-0.5 text-[0.65rem] font-bold text-primary">
                          실손
                        </span>
                      </span>
                      <span className="mt-0.5 block truncate text-xs font-medium text-muted">
                        영수증의 비급여 금액
                      </span>
                    </span>

                    <span className="flex shrink-0 items-center gap-1">
                      <input
                        inputMode="numeric"
                        value={formatComma(nonCovered)}
                        onChange={event => setNonCovered(onlyDigits(event.target.value))}
                        placeholder="0"
                        className="w-24 rounded-xl border border-line bg-surface px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
                      />
                      <span className="text-sm font-medium text-muted">원</span>
                    </span>
                  </label>
                </>
              )}
            </div>

            <Button
              type="button"
              size="lg"
              className="mt-3 w-full"
              disabled={submitting || (filledAmountCount === 0 && !hasMedicalCostInput)}
              onClick={handleApply}
            >
              {submitting ? '계산 중...' : '예상 보험금 계산하기'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
