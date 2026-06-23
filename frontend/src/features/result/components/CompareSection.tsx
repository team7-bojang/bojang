import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { cn } from '@/lib/utils';

import type { AnalysisCompareItem, AnalysisCompareScenario } from '../model';
import { formatWon } from '../utils/format';
import { inferInsurerId } from '../utils/resultAnalysis';

function scenarioLabel(scenario: AnalysisCompareScenario | undefined) {
  if (!scenario) {
    return '-';
  }
  if (scenario.status === 'eligible') {
    return `${formatWon(scenario.estimated_amount)}원`;
  }
  if (scenario.status === 'boundary_not_met') {
    return '조건 미달';
  }
  if (scenario.status === 'not_applicable') {
    return '해당 없음';
  }
  return scenario.estimated_amount > 0 ? `${formatWon(scenario.estimated_amount)}원` : '조건 미달';
}

function CompareRow({ item }: { item: AnalysisCompareItem }) {
  const current = item.scenarios.at(0);
  const target = item.scenarios.at(-1);
  const additional = Math.max(
    0,
    (target?.estimated_amount ?? 0) - (current?.estimated_amount ?? 0)
  );
  const insurerId = inferInsurerId(item.policy_name);

  return (
    <article className="grid w-full grid-cols-[auto_minmax(0,1fr)] gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center sm:gap-5">
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{item.rider_name}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">
          {item.policy_name}
        </span>
        <span className="mt-2 grid gap-2 text-sm font-semibold text-muted sm:grid-cols-2">
          <span>
            현재 {current?.days ?? '-'}일 {scenarioLabel(current)}
          </span>
          <span>
            목표 {target?.days ?? '-'}일 {scenarioLabel(target)}
          </span>
        </span>
        <span className="mt-2 line-clamp-2 block text-sm leading-6 text-muted">
          {target?.calc ?? current?.calc ?? ''}
        </span>
      </span>
      <span className="col-span-2 text-right sm:col-span-1">
        <span
          className={cn('block text-lg font-black', additional > 0 ? 'text-ink' : 'text-red-600')}
        >
          {additional > 0 ? `+${formatWon(additional)}원` : '추가 없음'}
        </span>
      </span>
    </article>
  );
}

export function CompareSection({ comparison }: { comparison: AnalysisCompareItem[] }) {
  return (
    <section className="animate-result-enter mt-4" style={{ animationDelay: '90ms' }}>
      <h2 className="text-xl font-black text-ink">
        추가 보장 시나리오 <span className="text-primary">{comparison.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {comparison.length > 0 ? (
          comparison.map((item, index) => (
            <CompareRow key={`${item.policy_name}-${item.rider_name}-${index}`} item={item} />
          ))
        ) : (
          <p className="py-6 text-sm font-semibold text-muted">
            추가 보장 비교 결과를 확인하지 못했습니다.
          </p>
        )}
      </div>
    </section>
  );
}
