import { cn } from '@/lib/utils';
import { X } from 'lucide-react';
import type { ReactNode } from 'react';

import type { Benefit } from '../types';
import { formatWon } from '../utils/format';

function DetailSection({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl bg-canvas/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-black text-ink">{title}</h4>
        {action}
      </div>
      {children}
    </section>
  );
}

function HighlightedQuote({ quote, highlight }: { quote: string; highlight: string }) {
  const [beforeHighlight, afterHighlight] = quote.split(highlight);

  if (!afterHighlight) {
    return <>{quote}</>;
  }

  return (
    <>
      {beforeHighlight}
      <mark className="rounded-sm bg-primary-tint px-1 py-0.5 text-ink">{highlight}</mark>
      {afterHighlight}
    </>
  );
}

export function AnalysisModal({ benefit, onClose }: { benefit: Benefit; onClose: () => void }) {
  const { analysis } = benefit;
  const decisionColor =
    analysis.decision === '청구 가능'
      ? 'bg-success-tint text-success'
      : analysis.decision === '조건 미달'
        ? 'bg-red-50 text-red-700'
        : 'bg-amber-50 text-amber-700';

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-ink/55 px-4 py-10 backdrop-blur-sm sm:py-[7vh]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="analysis-modal-title"
      onMouseDown={onClose}
    >
      <div
        className="max-h-[84vh] w-full max-w-2xl overflow-y-auto rounded-card bg-surface p-5 shadow-2xl ring-1 scrollbar-hide ring-line sm:p-6"
        onMouseDown={event => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 id="analysis-modal-title" className="text-xl font-black text-ink sm:text-2xl">
              {analysis.clauseTitle}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-canvas text-ink transition-colors hover:bg-primary-tint"
            aria-label="상세 분석 닫기"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="mt-5 space-y-3">
          <DetailSection title="보험상품명">
            <p className="mt-3 text-base font-black text-ink">{benefit.policyName}</p>
          </DetailSection>

          <DetailSection
            title="판정 결과 및 설명"
            action={
              <span className={cn('rounded-full px-3 py-1 text-sm font-black', decisionColor)}>
                {analysis.decision}
              </span>
            }
          >
            <p className="mt-3 text-sm font-semibold leading-6 text-ink">
              {analysis.decisionDescription}
            </p>
          </DetailSection>

          <DetailSection title="계산내역">
            <dl className="mt-3 divide-y divide-line text-sm">
              <div className="flex items-center justify-between gap-4 py-2 first:pt-0">
                <dt className="font-semibold text-ink">약관상 지급 기준</dt>
                <dd className="text-right font-black text-ink">{analysis.paymentBasis}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 py-2">
                <dt className="font-semibold text-ink">적용 기간</dt>
                <dd className="text-right font-black text-ink">{analysis.period}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 py-2">
                <dt className="font-semibold text-ink">계산식</dt>
                <dd className="text-right font-black text-ink">{analysis.formula}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 pt-2">
                <dt className="font-semibold text-ink">예상 보험금</dt>
                <dd className="text-right text-lg font-black text-primary">
                  {formatWon(analysis.expectedAmount)}원
                </dd>
              </div>
            </dl>
          </DetailSection>

          <DetailSection title="결제내역 기반 계산">
            <p className="mt-3 text-sm font-semibold leading-6 text-ink">
              {analysis.paymentCalculationDescription}
            </p>
          </DetailSection>

          <DetailSection title="약관 근거조항">
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <p className="min-w-0 flex-1 text-sm font-black text-ink">
                {benefit.insurerName} · {analysis.clauseTitle}
              </p>
              <span className="rounded-full bg-primary-tint px-3 py-1 text-xs font-black text-primary">
                {analysis.clausePage}
              </span>
            </div>
            <blockquote className="mt-4 border-l-4 border-primary bg-surface px-4 py-3 text-sm font-semibold leading-7 text-ink">
              <HighlightedQuote quote={analysis.clauseQuote} highlight={analysis.clauseHighlight} />
            </blockquote>
          </DetailSection>
        </div>
      </div>
    </div>
  );
}
