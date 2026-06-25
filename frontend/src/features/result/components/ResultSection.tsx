import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { cn } from '@/lib/utils';

import type { AnalysisSearchResult } from '../model';
import { formatWon } from '../utils/format';
import { inferInsurerId, isConditional, isEligible } from '../utils/resultAnalysis';

function statusText(result: AnalysisSearchResult) {
  if (isEligible(result)) {
    // 가입금액이 입력된 경우 예상 보험금, 미입력(0)이면 지급 가능 여부만 안내
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
    return 'text-ink';
  }
  if (isConditional(result)) {
    return 'text-amber-600';
  }
  return 'text-red-600';
}

function ResultRow({ result }: { result: AnalysisSearchResult }) {
  const insurerId = inferInsurerId(result.policy);

  return (
    <article className="grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:gap-5">
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{result.rider}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">{result.policy}</span>
        <span className="mt-2 line-clamp-2 block text-sm leading-6 text-muted">
          {result.explanation}
        </span>
      </span>
      <span className="text-right">
        <span className={cn('block text-lg font-black', statusTone(result))}>
          {statusText(result)}
        </span>
        <span className="mt-1 hidden text-sm font-medium text-muted sm:block">
          {result.calc ?? result.evidence?.article ?? ''}
        </span>
      </span>
    </article>
  );
}

interface ResultSectionProps {
  title: string;
  countClassName: string;
  results: AnalysisSearchResult[];
  emptyText: string;
  delay: string;
  className?: string;
}

export function ResultSection({
  title,
  countClassName,
  results,
  emptyText,
  delay,
  className,
}: ResultSectionProps) {
  return (
    <section className={cn('animate-result-enter', className)} style={{ animationDelay: delay }}>
      <h2 className="text-xl font-black text-ink">
        {title} <span className={countClassName}>{results.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {results.length > 0 ? (
          results.map((result, index) => (
            <ResultRow key={`${result.policy}-${result.rider}-${index}`} result={result} />
          ))
        ) : (
          <p className="py-6 text-sm font-semibold text-muted">{emptyText}</p>
        )}
      </div>
    </section>
  );
}
