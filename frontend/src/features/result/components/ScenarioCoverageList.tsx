import { ChevronRight } from 'lucide-react';

import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { cn } from '@/lib/utils';

import type { AnalysisSearchResult } from '../model';
import {
  becomesDailyClaimableAt,
  dayLabel,
  inferInsurerId,
  isDailyClaimableNow,
} from '../utils/resultAnalysis';

interface ScenarioCoverageListProps {
  results: AnalysisSearchResult[];
  currentDays: number;
  targetDays: number;
  /** 행 클릭 시 상세 분석 모달을 연다(CASE1 보장 목록과 동일). */
  onSelect?: (result: AnalysisSearchResult) => void;
}

// CASE1 보장 목록(ResultSection)과 동일한 행 그리드 — 로고 · 특약/상품명 · 우측 상태.
const ROW_GRID =
  'grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 px-4 py-4 text-left sm:gap-5 sm:px-6';

/** 보장 한 줄. highlight=true 면 '더 입원하면 추가되는 보장'으로 우측 상태를 강조한다.
 *  onSelect 가 있으면 CASE1 보장 목록처럼 클릭 가능한 버튼(상세 모달)로 렌더한다. */
function RiderRow({
  result,
  status,
  highlight,
  onSelect,
}: {
  result: AnalysisSearchResult;
  status: string;
  highlight: boolean;
  onSelect?: (result: AnalysisSearchResult) => void;
}) {
  const insurerId = inferInsurerId(result.policy);
  const body = (
    <>
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{result.rider}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">{result.policy}</span>
      </span>
      <span
        className={cn(
          'shrink-0 whitespace-nowrap text-right text-sm font-extrabold',
          highlight ? 'rounded-full bg-primary-tint px-2.5 py-1 text-primary' : 'text-primary'
        )}
      >
        {status}
      </span>
      {onSelect && <ChevronRight className="size-5 shrink-0 text-muted" />}
    </>
  );

  if (!onSelect) {
    return <article className={ROW_GRID}>{body}</article>;
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
      {body}
    </button>
  );
}

/** 보장 한 묶음(헤더 + 카드). 행 사이 구분선은 양 옆을 들여 카드 끝까지 닿지 않게 한다(ResultSection 동일). */
function CoverageGroup({
  results,
  title,
  subtitle,
  statusOf,
  highlight,
  onSelect,
}: {
  results: AnalysisSearchResult[];
  title: React.ReactNode;
  subtitle?: string;
  statusOf: (result: AnalysisSearchResult) => string;
  highlight: boolean;
  onSelect?: (result: AnalysisSearchResult) => void;
}) {
  return (
    <section className="animate-result-enter">
      <h2 className="text-xl font-extrabold text-ink">{title}</h2>
      {subtitle && <p className="mt-1 text-sm font-medium text-muted">{subtitle}</p>}
      <div className="mt-3 overflow-hidden rounded-card bg-surface shadow-sm">
        {results.map((result, index) => (
          <div key={result.rider_id ?? result.rider}>
            {index > 0 && <div className="mx-4 border-t border-line/80 sm:mx-6" />}
            <RiderRow
              result={result}
              status={statusOf(result)}
              highlight={highlight}
              onSelect={onSelect}
            />
          </div>
        ))}
      </div>
    </section>
  );
}

/** CASE2 보장 목록 — 현재 입원일수에 받을 수 있는 보장과, 더 입원하면 새로 추가되는 보장을 나눠 보여준다. */
export function ScenarioCoverageList({
  results,
  currentDays,
  targetDays,
  onSelect,
}: ScenarioCoverageListProps) {
  const claimableNow = results.filter(isDailyClaimableNow);
  const addedAtTarget = results.filter(r => becomesDailyClaimableAt(r, currentDays, targetDays));
  // 목표일수가 현재보다 크고, 늘려서 새로 생기는 보장이 있을 때만 '추가' 묶음을 보여준다.
  const hasAddition = targetDays > currentDays && addedAtTarget.length > 0;

  // 추가 보장이 실제로 청구 가능해지는 입원일수(임계일수 = 현재일수 + gap_days).
  // 예: 현재 3일 + gap 1 = 4일차부터. 라벨에 목표일수(의사권고)가 아니라 이 임계일수를 쓴다.
  const startDayOf = (result: AnalysisSearchResult) => currentDays + (result.gap_days ?? 0);
  const uniqueStartDays = [...new Set(addedAtTarget.map(startDayOf))];
  const addedTitle =
    uniqueStartDays.length === 1
      ? `${uniqueStartDays[0]}일 이상 입원하면 추가되는 보장`
      : '더 입원하면 추가되는 보장';

  return (
    <>
      {claimableNow.length > 0 && (
        <CoverageGroup
          results={claimableNow}
          title={
            <>
              현재 {dayLabel(currentDays)}에 받을 수 있는 보장{' '}
              <span className="text-primary">{claimableNow.length}개</span>
            </>
          }
          statusOf={() => '지급 가능'}
          highlight={false}
          onSelect={onSelect}
        />
      )}

      {hasAddition && (
        <CoverageGroup
          results={addedAtTarget}
          title={
            <>
              {addedTitle} <span className="text-primary">{addedAtTarget.length}개</span>
            </>
          }
          subtitle={`의사 권고 입원 기간(${targetDays}일)까지 입원하면 받을 수 있어요`}
          statusOf={result => `${startDayOf(result)}일 이상`}
          highlight
          onSelect={onSelect}
        />
      )}
    </>
  );
}
