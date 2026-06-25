import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { cn } from '@/lib/utils';

import type { AnalysisSearchResult } from '../model';
import { formatWon } from '../utils/format';
import { inferInsurerId, isConditional, isEligible } from '../utils/resultAnalysis';

interface PreviewCalculation {
  amount: number;
  formula: string;
  basis: string;
}

function statusText(result: AnalysisSearchResult, previewCalculation?: PreviewCalculation | null) {
  if (isEligible(result)) {
    // 가입금액이 입력된 경우 예상 보험금, 미입력(0)이면 지급 가능 여부만 안내
    if (previewCalculation) {
      return `${formatWon(previewCalculation.amount)}원`;
    }
    return result.estimated_amount > 0 ? `${formatWon(result.estimated_amount)}원` : '지급 가능';
  }
  if (isConditional(result)) {
    return '조건 확인';
  }
  if (result.status === 'not_applicable') {
    return '해당 없음';
  }
  if (result.missed) {
    return '놓친 보장';
  }
  return '조건 미달';
}

function statusTone(result: AnalysisSearchResult) {
  if (isEligible(result)) {
    return 'text-primary';
  }
  if (isConditional(result)) {
    return 'text-amber-600';
  }
  return 'text-red-600';
}

function ResultRowBody({
  result,
  previewCalculation,
}: {
  result: AnalysisSearchResult;
  previewCalculation?: PreviewCalculation | null;
}) {
  const insurerId = inferInsurerId(result.policy);

  return (
    <>
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{result.rider}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">{result.policy}</span>
      </span>
      <span className="text-right">
        <span className={cn('block text-lg font-extrabold', statusTone(result))}>
          {statusText(result, previewCalculation)}
        </span>
        {/* 청구 가능하지만 예상 보험금이 아직 산출되지 않은 경우(가입금액 미입력)에만 안내 */}
        {isEligible(result) && result.estimated_amount <= 0 && (
          <span className="mt-1 block truncate text-sm font-medium text-muted">
            가입 금액을 입력하시면 예상 보험금 계산이 가능합니다.
          </span>
        )}
      </span>
    </>
  );
}

const ROW_GRID =
  'grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 px-4 py-4 text-left sm:gap-5 sm:px-6';

function ResultRow({
  result,
  onSelect,
  previewCalculation,
}: {
  result: AnalysisSearchResult;
  onSelect?: (result: AnalysisSearchResult) => void;
  previewCalculation?: PreviewCalculation | null;
}) {
  if (!onSelect) {
    return (
      <article className={ROW_GRID}>
        <ResultRowBody result={result} previewCalculation={previewCalculation} />
      </article>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onSelect(result)}
      className={cn(
        ROW_GRID,
        'grid-cols-[auto_minmax(0,1fr)_auto_auto] transition-colors hover:bg-canvas/70'
      )}
      aria-label={`${result.rider} 상세 분석 보기`}
    >
      <ResultRowBody result={result} previewCalculation={previewCalculation} />
      <ChevronRight className="size-5 shrink-0 text-muted" />
    </button>
  );
}

interface ResultSectionProps {
  title: string;
  countClassName: string;
  results: AnalysisSearchResult[];
  emptyText: string;
  delay: string;
  className?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  onSelect?: (result: AnalysisSearchResult) => void;
  getPreviewCalculation?: (result: AnalysisSearchResult) => PreviewCalculation | null;
}

export function ResultSection({
  title,
  countClassName,
  results,
  emptyText,
  delay,
  className,
  collapsible = false,
  defaultOpen = true,
  onSelect,
  getPreviewCalculation,
}: ResultSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const visible = !collapsible || open;

  // 행 목록 — 행 사이 구분선은 양 옆을 들여(mx) 카드 끝까지 닿지 않게 한다.
  const rows =
    results.length > 0 ? (
      results.map((result, index) => (
        <div key={`${result.policy}-${result.rider}-${index}`}>
          {index > 0 && <div className="mx-4 border-t border-line/80 sm:mx-6" />}
          <ResultRow
            result={result}
            onSelect={onSelect}
            previewCalculation={getPreviewCalculation?.(result)}
          />
        </div>
      ))
    ) : (
      <p className="px-4 py-6 text-sm font-semibold text-muted sm:px-6">{emptyText}</p>
    );

  if (collapsible) {
    return (
      <section className={cn('animate-result-enter', className)} style={{ animationDelay: delay }}>
        <div className="overflow-hidden rounded-card bg-surface shadow-sm">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left transition-colors hover:bg-canvas/50 sm:px-6"
            onClick={() => setOpen(prev => !prev)}
            aria-expanded={open}
          >
            <span className="min-w-0">
              <span className="block text-lg font-extrabold text-ink">
                {title} <span className={countClassName}>{results.length}개</span>
              </span>
              <span className="mt-1 block text-xs font-semibold text-muted">
                {open ? '목록 접기' : '목록 펼치기'}
              </span>
            </span>
            <ChevronDown
              className={cn(
                'size-5 shrink-0 text-muted transition-transform',
                open && 'rotate-180'
              )}
              aria-hidden="true"
            />
          </button>

          {visible && <div className="border-t border-line">{rows}</div>}
        </div>
      </section>
    );
  }

  return (
    <section className={cn('animate-result-enter', className)} style={{ animationDelay: delay }}>
      <h2 className="text-xl font-extrabold text-ink">
        {title} <span className={countClassName}>{results.length}개</span>
      </h2>

      <div className="mt-3 overflow-hidden rounded-card bg-surface shadow-sm">{rows}</div>
    </section>
  );
}
