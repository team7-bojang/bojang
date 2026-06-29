import { cn } from '@/lib/utils';

import type { AnalysisSearchResult } from '../model';
import { becomesDailyClaimableAt, isDailyClaimableNow } from '../utils/resultAnalysis';

interface ScenarioCompareGraphProps {
  results: AnalysisSearchResult[];
  /** 현재 입원일수 (admission_days_current). */
  currentDays: number;
  /** 의사 권고 입원일수 (admission_days_diagnosed). */
  targetDays: number;
}

function dayLabel(days: number) {
  return days <= 1 ? '첫날' : `${days}일차`;
}

/** 입원 기간별 보장 항목 수 막대 — 현재일수(기본) 대비 목표일수(추가)를 한 줄에 쌓아 보여준다. */
function CountBar({
  label,
  base,
  added,
  max,
  tone,
}: {
  label: string;
  base: number;
  added: number;
  max: number;
  tone: 'muted' | 'primary';
}) {
  const pct = (value: number) => (max > 0 ? (value / max) * 100 : 0);
  return (
    <div className="flex items-center gap-3">
      <span className="w-12 shrink-0 text-sm font-bold text-muted">{label}</span>
      <div className="relative h-7 flex-1 overflow-hidden rounded-full bg-canvas">
        <div className="flex h-full">
          <div
            className={cn(
              'flex h-full items-center justify-end pr-2 text-xs font-extrabold text-white',
              tone === 'primary' ? 'bg-primary' : 'bg-primary/70'
            )}
            style={{ width: `${pct(base)}%` }}
          >
            {base > 0 ? `${base}개` : ''}
          </div>
          {added > 0 && (
            <div
              className="flex h-full items-center justify-center bg-primary-tint px-2 text-xs font-extrabold text-primary"
              style={{ width: `${pct(added)}%` }}
            >
              +{added}개
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** 보장 한 줄. isNew=true 면 '이 일수에 새로 추가된 보장'으로 강조한다. */
function RiderRow({
  result,
  badge,
  isNew,
}: {
  result: AnalysisSearchResult;
  badge: string;
  isNew: boolean;
}) {
  return (
    <div
      className={cn(
        'px-3 py-3',
        isNew
          ? 'rounded-xl bg-primary-tint/50 ring-1 ring-primary/20'
          : 'border-b border-line/70 last:border-b-0'
      )}
    >
      <span className="mb-1 flex">
        <span
          className={cn(
            'shrink-0 rounded-full px-2 py-0.5 text-[0.7rem] font-bold',
            isNew ? 'bg-primary text-white' : 'bg-canvas text-muted'
          )}
        >
          {badge}
        </span>
      </span>
      <span className="block truncate text-sm font-bold text-ink">{result.rider}</span>
      <span className="block truncate text-xs font-medium text-muted">{result.explanation}</span>
    </div>
  );
}

/** CASE2 결과 — 현재 입원일수 vs 의사 권고일수로, 더 입원하면 어떤 보장이 새로 추가되는지 비교·강조한다. */
export function ScenarioCompareGraph({
  results,
  currentDays,
  targetDays,
}: ScenarioCompareGraphProps) {
  const claimableNow = results.filter(isDailyClaimableNow);
  const addedAtTarget = results.filter(r => becomesDailyClaimableAt(r, currentDays, targetDays));

  const baseCount = claimableNow.length;
  const addedCount = addedAtTarget.length;
  const targetCount = baseCount + addedCount;
  // 목표일수가 현재보다 크고, 늘려서 새로 생기는 보장이 있을 때만 '추가' 강조를 보여준다.
  const hasAddition = targetDays > currentDays && addedCount > 0;

  // 추가 보장이 실제로 청구 가능해지는 입원일수(임계일수 = 현재일수 + gap_days).
  // 예: 현재 3일 + gap 1 = 4일차부터. 라벨에 목표일수(의사권고)가 아니라 이 임계일수를 쓴다.
  const startDayOf = (result: AnalysisSearchResult) => currentDays + (result.gap_days ?? 0);
  const uniqueStartDays = [...new Set(addedAtTarget.map(startDayOf))];
  const addedHeaderLabel =
    uniqueStartDays.length === 1
      ? `${uniqueStartDays[0]}일 이상 입원하면 추가되는 보장`
      : '더 입원하면 추가되는 보장';
  // 의사 권고 입원 기간(목표일수)을 노출해, 권고만큼 입원하면 받게 됨을 안내한다.
  const addedSubtitle = `의사 권고 입원 기간(${targetDays}일)까지 입원하면 받을 수 있어요`;

  return (
    <div className="mt-4 space-y-4">
      <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
        <h2 className="text-lg font-black text-ink">입원 기간별 보장 항목 수</h2>
        <p className="mt-1 text-sm font-medium text-muted">
          입원 기간에 따라 받을 수 있는 입원일당 보장이 달라져요
        </p>
        <div className="mt-5 space-y-3">
          <CountBar
            label={dayLabel(currentDays)}
            base={baseCount}
            added={0}
            max={Math.max(targetCount, 1)}
            tone="muted"
          />
          {hasAddition && (
            <CountBar
              label={dayLabel(targetDays)}
              base={baseCount}
              added={addedCount}
              max={Math.max(targetCount, 1)}
              tone="primary"
            />
          )}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs font-semibold text-muted">
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-primary" />
            {dayLabel(currentDays)} 보장
          </span>
          {hasAddition && (
            <span className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-full bg-primary-tint" />
              추가되는 보장
            </span>
          )}
        </div>
      </section>

      {baseCount > 0 && (
        <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
          <h2 className="text-base font-black text-ink">
            <span className="mr-1.5 font-tossface">💬</span>
            현재 {dayLabel(currentDays)}에 받을 수 있는 보장
            <span className="ml-1.5 text-primary">{baseCount}개</span>
          </h2>
          <div className="mt-3">
            {claimableNow.map(result => (
              <RiderRow
                key={result.rider_id ?? result.rider}
                result={result}
                badge="지급 청구 가능"
                isNew={false}
              />
            ))}
          </div>
        </section>
      )}

      {hasAddition && (
        <section className="animate-result-enter rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
          <h2 className="text-base font-black text-ink">
            <span className="mr-1.5 font-tossface">✨</span>
            {addedHeaderLabel}
            <span className="ml-1.5 text-primary">{addedCount}개</span>
          </h2>
          <p className="mt-1 text-sm font-medium text-muted">{addedSubtitle}</p>
          {/* 현재일수엔 없고, 더 입원하면 새로 생기는 보장만(중복 없이) 강조한다. */}
          <div className="mt-3 space-y-2">
            {addedAtTarget.map(result => (
              <RiderRow
                key={result.rider_id ?? result.rider}
                result={result}
                badge={`${startDayOf(result)}일 이상 입원 시`}
                isNew
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
