import { TrendingUp } from 'lucide-react';

import type { AnalysisSearchResult } from '../model';
import { becomesDailyClaimableAt, dayLabel, isDailyClaimableNow } from '../utils/resultAnalysis';

interface ScenarioCompareGraphProps {
  results: AnalysisSearchResult[];
  /** 현재 입원일수 (admission_days_current). */
  currentDays: number;
  /** 의사 권고 입원일수 (admission_days_diagnosed). */
  targetDays: number;
}

/** CASE2 그래프 — 현재 입원일수 vs 의사 권고일수의 입원일당 보장 항목 수를 세로 막대로 비교한다. */
export function ScenarioCompareGraph({
  results,
  currentDays,
  targetDays,
}: ScenarioCompareGraphProps) {
  const baseCount = results.filter(isDailyClaimableNow).length;
  const addedCount = results.filter(r =>
    becomesDailyClaimableAt(r, currentDays, targetDays)
  ).length;
  const targetCount = baseCount + addedCount;
  // 목표일수가 현재보다 크고, 늘려서 새로 생기는 보장이 있을 때만 '추가' 강조를 보여준다.
  const hasAddition = targetDays > currentDays && addedCount > 0;
  // 막대 높이 비율 — 가장 큰 목표 보장 수(없으면 1)를 기준으로 0~100%.
  const pct = (value: number) => (value / Math.max(targetCount, 1)) * 100;

  return (
    <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
      <h2 className="text-lg font-black text-ink">입원 기간별 보장 항목 수</h2>
      <p className="mt-1 text-sm font-medium text-muted">
        입원 기간에 따라 받을 수 있는 입원일당 보장이 달라져요
      </p>

      {/* 현재 입원일수 vs 목표 입원일수 — 세로 막대로 보장 항목 수 변화를 비교한다. */}
      <div className="mt-8 flex items-end justify-center gap-8 sm:gap-14">
        {/* 현재 일수 */}
        <div className="flex flex-col items-center">
          <span className="text-sm font-black text-muted">{dayLabel(currentDays)}</span>
          <span className="mt-1 text-2xl font-black text-ink">{baseCount}개</span>
          <div className="mt-3 flex h-44 w-24 items-end sm:h-56 sm:w-28">
            <div
              className="animate-coverage-bar-rise w-full overflow-hidden rounded-t-xl bg-chart-base"
              style={{
                height: `${pct(baseCount)}%`,
                minHeight: baseCount > 0 ? '2.5rem' : undefined,
              }}
            />
          </div>
        </div>

        {/* 더 입원하면 추가되는 보장 — 증가분 강조 */}
        {hasAddition && (
          <>
            <div className="mb-16 flex flex-col items-center text-center sm:mb-20">
              <TrendingUp className="size-6 text-chart-gain" />
              <span className="mt-1 text-sm font-black text-primary">+{addedCount}개</span>
              <span className="text-xs font-bold text-muted">추가 가능</span>
            </div>

            {/* 목표 일수 — 기존 보장(아래) + 추가 보장(위)을 쌓아 보여준다. */}
            <div className="flex flex-col items-center">
              <span className="text-sm font-black text-primary">{dayLabel(targetDays)}</span>
              <span className="mt-1 text-2xl font-black text-primary">{targetCount}개</span>
              <div className="mt-3 flex h-44 w-24 items-end sm:h-56 sm:w-28">
                <div
                  className="animate-coverage-bar-rise flex w-full flex-col overflow-hidden rounded-t-xl"
                  style={{ height: `${pct(targetCount)}%` }}
                >
                  <div
                    className="bg-chart-gain"
                    style={{ height: `${pct(addedCount)}%`, minHeight: '2rem' }}
                  />
                  <div
                    className="flex-1 bg-chart-base"
                    style={{ minHeight: baseCount > 0 ? '2.5rem' : undefined }}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5 text-xs font-semibold text-muted">
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-chart-base" />
          현재 보장
        </span>
        {hasAddition && (
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-chart-gain" />
            추가되는 보장
          </span>
        )}
      </div>
    </section>
  );
}
