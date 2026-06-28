import { ChevronUp } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { type InsurerId } from '@/features/insurance/data/insurers';
import { cn } from '@/lib/utils';

import { formatWon } from '../utils/format';

export interface CoverageGroupRow {
  /** 입력 단위 키: `${policy}|${kind}`. 같은 상품이라도 일당/정액은 단위가 달라 따로 입력받는다. */
  key: string;
  policy: string;
  insurerId: InsurerId;
  /** daily=입원일당(1일당 단가) · fixed=진단/정액(가입금액) */
  kind: 'daily' | 'fixed';
  /** 이 그룹에 속한 청구 가능 특약명 목록(표시용). */
  riders: string[];
}

interface CoverageAmountFormProps {
  groups: CoverageGroupRow[];
  /** 이미 입력된 값(groupKey → amount). 값을 복원한다. */
  initialAmounts: Record<string, number>;
  /** 현재 예상 보험금 합계(미산출이면 null). */
  expectedAmount: number | null;
  submitting: boolean;
  /** 입력된 그룹별 금액 전체를 한 번에 전달한다(groupKey → amount). */
  onApply: (amounts: Record<string, number>) => void;
  /** 하단 고정 패널의 실제 높이를 알려준다(본문 하단 여백 확보용). */
  onMeasure?: (height: number) => void;
}

const onlyDigits = (value: string) => value.replace(/[^0-9]/g, '');
const formatComma = (digits: string) => (digits ? Number(digits).toLocaleString('ko-KR') : '');

/** 청구 가능한 정액 보장의 가입금액/일당 단가를 화면 하단 고정 패널에서 바로 입력받아 한 번에 재계산한다.
 *  입원일당(1일당 단가)과 진단/정액(가입금액)은 단위가 다르므로 그룹을 나눠 입력받는다.
 *  (실손은 병원비 기준이라 여기서 다루지 않는다.) */
export function CoverageAmountForm({
  groups,
  initialAmounts,
  expectedAmount,
  submitting,
  onApply,
  onMeasure,
}: CoverageAmountFormProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      groups.map(g => [g.key, initialAmounts[g.key] ? String(initialAmounts[g.key]) : ''])
    )
  );

  // 고정 패널 높이를 측정해 부모(본문)가 하단 여백을 확보하도록 알린다.
  useEffect(() => {
    const el = panelRef.current;
    if (!el || !onMeasure) {
      return;
    }
    const update = () => onMeasure(el.offsetHeight);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, [onMeasure, groups.length]);

  const filledCount = useMemo(
    () => Object.values(values).filter(digits => Number(digits) > 0).length,
    [values]
  );

  if (groups.length === 0) {
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
    onApply(amounts);
  };

  // 입력 중(패널 내부 포커스)에는 마우스가 벗어나도 닫지 않는다.
  const closeIfNotEditing = () => {
    const el = panelRef.current;
    if (el && el.contains(document.activeElement)) {
      return;
    }
    setOpen(false);
  };

  const hasAmount = expectedAmount !== null && expectedAmount > 0;

  return (
    <div
      ref={panelRef}
      className="fixed inset-x-0 bottom-0 z-40 overflow-hidden rounded-t-[1.75rem] border border-b-0 border-line bg-surface shadow-[0_-8px_28px_rgba(11,18,32,0.10)]"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={closeIfNotEditing}
    >
      <div className="mx-auto flex max-h-[calc(100svh-5rem)] max-w-5xl flex-col px-5 py-3 sm:px-8">
        {/* 핸들 — 평소엔 접혀 있고, 호버하면 자동으로 열린다(탭으로도 토글). */}
        <button
          type="button"
          onClick={() => setOpen(prev => !prev)}
          className="flex w-full items-center justify-between gap-3 text-left"
          aria-expanded={open}
        >
          <span className="min-w-0">
            <span className="block text-md font-bold text-ink">
              {hasAmount ? '가입금액 수정하기' : '가입금액·일당 단가를 입력하면 바로 계산돼요'}
            </span>
            <span className="mt-0.5 block text-sm font-medium text-muted">
              입원일당은 1일당 단가, 진단·정액은 가입금액을 입력하세요
            </span>
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

        {/* drawer 본문 — grid-rows 0fr↔1fr 로 높이를 애니메이션해 내용이 잘리지 않게 한다. */}
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
                          {isDaily ? '입원일당 · 1일당 단가' : '가입금액'}
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
                      <span className="text-sm font-medium text-muted">
                        {isDaily ? '원/일' : '원'}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>

            <Button
              type="button"
              size="lg"
              className="mt-3 w-full"
              disabled={submitting || filledCount === 0}
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
