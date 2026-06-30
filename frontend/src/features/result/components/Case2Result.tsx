import type { AnalysisSearchResult } from '../model';
import { isDailyRider } from '../utils/resultAnalysis';
import { ScenarioCompareGraph } from './ScenarioCompareGraph';
import { ScenarioCoverageList } from './ScenarioCoverageList';

interface Case2ResultProps {
  results: AnalysisSearchResult[];
  scenarioDays: { current: number; target: number } | null;
  /** 보장 행 클릭 시 상세 모달을 연다(CASE1과 동일). */
  onSelect?: (result: AnalysisSearchResult) => void;
}

// CASE2 는 금액 입력·예상금액 없이 입원 기간(현재 vs 의사 권고)별 보장 변화만 보여준다.
export function Case2Result({ results, scenarioDays, onSelect }: Case2ResultProps) {
  if (!results.some(isDailyRider)) {
    return (
      <p className="mt-6 rounded-card bg-surface p-6 text-center text-sm font-semibold text-muted shadow-sm ring-1 ring-line">
        입원 기간에 따라 달라지는 입원일당 보장이 확인되지 않았습니다.
      </p>
    );
  }
  if (!scenarioDays) {
    return null;
  }
  return (
    <div className="mt-4 space-y-4">
      <ScenarioCompareGraph
        results={results}
        currentDays={scenarioDays.current}
        targetDays={scenarioDays.target}
      />
      <ScenarioCoverageList
        results={results}
        currentDays={scenarioDays.current}
        targetDays={scenarioDays.target}
        onSelect={onSelect}
      />
    </div>
  );
}
