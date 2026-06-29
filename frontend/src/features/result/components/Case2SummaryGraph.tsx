import { cn } from '@/lib/utils';

import type { Case2Summary, Case2SummaryItem } from '../model';
import { formatWon } from '../utils/format';

type Tone = 'muted' | 'primary' | 'danger';

const FILL: Record<Tone, string> = {
  muted: 'bg-line',
  primary: 'bg-primary',
  danger: 'bg-orange-500',
};
const TEXT: Record<Tone, string> = {
  muted: 'text-muted',
  primary: 'text-primary',
  danger: 'text-orange-600',
};

interface BarSpec {
  label: string;
  amount: number;
  tone: Tone;
}

/** 두 금액을 막대 두 개로 비교하고 가운데에 증감액을 표시한다. */
function CompareBars({
  left,
  right,
  delta,
  deltaTone,
}: {
  left: BarSpec;
  right: BarSpec;
  delta: string;
  deltaTone: Tone;
}) {
  const max = Math.max(left.amount, right.amount, 1);
  const heightPct = (amount: number) => Math.max(8, Math.round((amount / max) * 100));

  return (
    <div className="relative flex items-end justify-center gap-10 pt-6 sm:gap-16">
      {[left, right].map((bar, index) => (
        <div key={index} className="flex w-24 flex-col items-center">
          <div className="flex h-40 w-full flex-col items-center justify-end">
            <span className={cn('mb-1.5 text-sm font-extrabold sm:text-base', TEXT[bar.tone])}>
              {formatWon(bar.amount)}원
            </span>
            <div
              className={cn('w-12 rounded-t-lg sm:w-16', FILL[bar.tone])}
              style={{ height: `${heightPct(bar.amount)}%` }}
            />
          </div>
          <span className="mt-2 text-center text-xs font-medium text-muted">{bar.label}</span>
        </div>
      ))}
      <span
        className={cn(
          'absolute left-1/2 top-1 -translate-x-1/2 rounded-full bg-surface px-2.5 py-0.5 text-sm font-bold shadow-sm ring-1 ring-line',
          TEXT[deltaTone]
        )}
      >
        {delta}
      </span>
    </div>
  );
}

function ItemRow({ item, tone }: { item: Case2SummaryItem; tone: Tone }) {
  const note = item.condition ?? item.reason;
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/70 py-3 last:border-b-0">
      <span className="min-w-0">
        <span className="block truncate text-sm font-bold text-ink">{item.rider}</span>
        <span className="block truncate text-xs font-medium text-muted">
          {item.policy}
          {note ? ` · ${note}` : ''}
        </span>
      </span>
      <span className={cn('shrink-0 text-sm font-extrabold', TEXT[tone])}>
        {tone === 'danger' ? '−' : '+'}
        {formatWon(item.amount)}원
      </span>
    </div>
  );
}

/** CASE2 결과 — 추가 보장(2-1)·감액(2-2)을 막대그래프로 보여준다. */
export function Case2SummaryGraph({ summary }: { summary: Case2Summary }) {
  const hasAdditional = summary.additional_total > 0;
  const hasReduced = summary.reduced_total > 0;
  const hasCurrent = summary.current_total > 0;

  if (!hasAdditional && !hasReduced && !hasCurrent) {
    return (
      <section className="mt-4 rounded-card bg-surface p-6 text-center shadow-sm ring-1 ring-line">
        <p className="text-sm font-semibold text-muted">청구 가능한 보장이 확인되지 않았습니다.</p>
        <p className="mt-1 text-xs font-medium text-muted">
          가입금액·병원비를 입력하면 예상 보험금을 계산해드려요.
        </p>
      </section>
    );
  }

  return (
    <div className="mt-4 space-y-4">
      {/* 현재 받을 수 있는 보험금 — 항상 표시(가입금액 입력 반영) */}
      <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
        <p className="text-sm font-bold text-muted">현재 받을 수 있는 보험금</p>
        <p className="mt-1 text-2xl font-black text-primary">
          {formatWon(summary.current_total)}원
        </p>
        {!hasAdditional && !hasReduced && (
          <p className="mt-1 text-xs font-medium text-muted">
            추가로 받거나 감액될 수 있는 보장은 확인되지 않았습니다.
          </p>
        )}
      </section>

      {hasAdditional && (
        <section className="animate-result-enter rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
          <h2 className="text-lg font-black text-ink">✨ 추가로 받을 수 있는 보장을 찾았어요</h2>
          <p className="mt-1 text-sm font-medium text-muted">조건을 채우면 더 받을 수도 있어요</p>
          <CompareBars
            left={{
              label: '현재 받을 수 있는 보험금',
              amount: summary.current_total,
              tone: 'muted',
            }}
            right={{
              label: '조건 충족 시 예상 보험금',
              amount: summary.potential_total,
              tone: 'primary',
            }}
            delta={`+${formatWon(summary.additional_total)}원`}
            deltaTone="primary"
          />
          {summary.additional_items.length > 0 && (
            <div className="mt-5">
              <p className="mb-1 text-sm font-bold text-ink">
                추가 보장 가능성 {summary.additional_items.length}개
              </p>
              {summary.additional_items.map((item, index) => (
                <ItemRow key={`${item.rider}-${index}`} item={item} tone="primary" />
              ))}
            </div>
          )}
        </section>
      )}

      {hasReduced && (
        <section className="animate-result-enter rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
          <h2 className="text-lg font-black text-ink">⚠️ 실제로 받는 보험금이 줄어들 수 있어요</h2>
          <p className="mt-1 text-sm font-medium text-muted">
            가입기간·면책기간 등 약관 기준에 따라 감액될 수 있어요
          </p>
          <CompareBars
            left={{
              label: '예상 받을 수 있는 보험금',
              amount: summary.before_reduction_total,
              tone: 'muted',
            }}
            right={{
              label: '실제 받을 수 있는 보험금',
              amount: summary.current_total,
              tone: 'danger',
            }}
            delta={`−${formatWon(summary.reduced_total)}원`}
            deltaTone="danger"
          />
          {summary.reduced_items.length > 0 && (
            <div className="mt-5">
              <p className="mb-1 text-sm font-bold text-ink">
                감액 사유 {summary.reduced_items.length}개
              </p>
              {summary.reduced_items.map((item, index) => (
                <ItemRow key={`${item.rider}-${index}`} item={item} tone="danger" />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
