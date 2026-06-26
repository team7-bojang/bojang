import { cn } from '@/lib/utils';
import { X } from 'lucide-react';
import { useEffect, type ReactNode } from 'react';

import type { Benefit } from '../model';
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
        <h4 className="text-md font-bold text-ink">{title}</h4>
        {action}
      </div>
      {children}
    </section>
  );
}

function HighlightedQuote({ quote, highlight }: { quote: string; highlight: string }) {
  if (!highlight) {
    return <>{quote}</>;
  }

  const [beforeHighlight, afterHighlight] = quote.split(highlight);

  if (afterHighlight === undefined) {
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

  // 모달이 열려 있는 동안 배경(body) 스크롤을 잠근다.
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, []);

  const decisionColor =
    analysis.decision === '청구 가능'
      ? 'bg-success-tint text-success'
      : analysis.decision === '조건 미달'
        ? 'bg-red-50 text-red-700'
        : 'bg-amber-50 text-amber-700';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/55 px-4 py-10 backdrop-blur-sm"
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
            <p className="text-sm font-semibold text-muted">{benefit.insurerName}</p>
            <h3 id="analysis-modal-title" className="mt-1 text-xl font-bold text-ink sm:text-2xl">
              {benefit.title}
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
            <p className="mt-3 text-base font-bold text-ink">{benefit.policyName}</p>
          </DetailSection>

          <DetailSection
            title="판정 결과 및 설명"
            action={
              <span className={cn('rounded-full px-3 py-1 text-sm font-bold', decisionColor)}>
                {analysis.decision}
              </span>
            }
          >
            <p className="mt-3 text-sm font-semibold leading-6 text-ink">
              {analysis.decisionDescription}
            </p>
          </DetailSection>

          {/* '확인 필요'(조건 확인 필요) 보장은 지급 여부가 미정이라 계산내역을 표시하지 않는다. */}
          {analysis.decision !== '확인 필요' && (
            <DetailSection title="계산내역">
              <dl className="mt-3 divide-y divide-line text-sm">
                {analysis.paymentBasis && (
                  <div className="flex items-center justify-between gap-4 py-2 first:pt-0">
                    <dt className="font-semibold text-ink">약관상 지급 기준</dt>
                    <dd className="text-right font-bold text-ink">{analysis.paymentBasis}</dd>
                  </div>
                )}
                {analysis.period && (
                  <div className="flex items-center justify-between gap-4 py-2 first:pt-0">
                    <dt className="font-semibold text-ink">적용 기간</dt>
                    <dd className="text-right font-bold text-ink">{analysis.period}</dd>
                  </div>
                )}
                {analysis.formula && (
                  <div className="flex items-center justify-between gap-4 py-2 first:pt-0">
                    <dt className="font-semibold text-ink">계산식</dt>
                    <dd className="text-right font-bold text-ink">{analysis.formula}</dd>
                  </div>
                )}
                <div className="flex items-center justify-between gap-4 py-2 first:pt-0">
                  <dt className="font-semibold text-ink">예상 보험금</dt>
                  <dd className="text-right text-lg font-bold text-primary">
                    {analysis.expectedAmount > 0
                      ? `${formatWon(analysis.expectedAmount)}원`
                      : '가입금액 입력 시 산출'}
                  </dd>
                </div>
              </dl>
            </DetailSection>
          )}

          {analysis.paymentCalculationDescription && (
            <DetailSection title="결제내역 기반 계산">
              <p className="mt-3 text-sm font-semibold leading-6 text-ink">
                {analysis.paymentCalculationDescription}
              </p>
            </DetailSection>
          )}

          <DetailSection title="약관 근거조항">
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <p className="min-w-0 flex-1 text-sm font-bold text-ink">
                {benefit.insurerName} · {analysis.clauseTitle}
              </p>
              {analysis.clausePage && (
                <span className="rounded-full bg-primary-tint px-3 py-1 text-xs font-bold text-primary">
                  {analysis.clausePage}
                </span>
              )}
            </div>
            {analysis.clauseQuote ? (
              <blockquote className="mt-4 border-l-4 border-primary bg-surface px-4 py-3 text-sm font-medium leading-7 text-ink">
                <HighlightedQuote
                  quote={analysis.clauseQuote}
                  highlight={analysis.clauseHighlight}
                />
              </blockquote>
            ) : (
              <p className="mt-4 text-sm font-medium text-muted">
                약관 원문이 제공되지 않았습니다.
              </p>
            )}
          </DetailSection>
        </div>
      </div>
    </div>
  );
}
