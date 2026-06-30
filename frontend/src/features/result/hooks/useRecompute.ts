import { useState } from 'react';

import { judgeCaseAnalysis } from '@/features/result/queries';

import type { AnalysisSearchResponse, CoverageAmountInput, MedicalCostInput } from '../model';

type UseRecomputeParams = {
  caseId: string;
  // 그룹 키 → 그 그룹에 속한 rider_id 목록(buildCoverageGroups 결과).
  groupRiderIds: Record<string, string[]>;
  setAnalysis: React.Dispatch<React.SetStateAction<AnalysisSearchResponse | null>>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  // 병원비(실손) 입력은 useResultData 가 소유한다(대시보드 기본값 로드와 공유).
  setMedicalCosts: React.Dispatch<React.SetStateAction<MedicalCostInput>>;
};

export type UseRecomputeReturn = {
  recomputing: boolean;
  // 그룹(상품×일당/정액)별 입력 가입금액. 폼 복원·합계 유지에 쓴다.
  coverageAmounts: Record<string, number>;
  handleApplyInputs: (amountsByGroup: Record<string, number>, costs: MedicalCostInput) => void;
};

// 가입금액(정액)·병원비(실손) 입력을 judge API 로 재계산하는 책임을 모은다.
// judge 재계산은 무상태라 매 호출에 두 입력을 모두 실어야 한쪽이 다른 쪽을 덮어쓰지 않는다.
// (DB 저장·RAG 재탐색·extracted-info 는 거치지 않는다)
export function useRecompute({
  caseId,
  groupRiderIds,
  setAnalysis,
  setError,
  setMedicalCosts,
}: UseRecomputeParams): UseRecomputeReturn {
  const [recomputing, setRecomputing] = useState(false);
  // 특약별 입력한 가입금액(groupKey → amount). 입력값을 누적해 전체 합계·다른 특약 금액을 유지한다.
  const [coverageAmounts, setCoverageAmounts] = useState<Record<string, number>>({});

  const recompute = async (amountsByGroup: Record<string, number>, medical: MedicalCostInput) => {
    if (!caseId) {
      return;
    }
    setRecomputing(true);
    try {
      const payload: CoverageAmountInput[] = [];
      for (const [key, amount] of Object.entries(amountsByGroup)) {
        for (const rider_id of groupRiderIds[key] ?? []) {
          payload.push({ rider_id, amount, amount_source: '결과화면 입력' });
        }
      }
      const refreshed = await judgeCaseAnalysis(
        caseId,
        payload.length > 0 ? payload : undefined,
        medical
      );
      setAnalysis(refreshed);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '예상 보험금 계산에 실패했습니다.');
    } finally {
      setRecomputing(false);
    }
  };

  const handleApplyInputs = (amountsByGroup: Record<string, number>, costs: MedicalCostInput) => {
    setCoverageAmounts(amountsByGroup);
    setMedicalCosts(costs);
    void recompute(amountsByGroup, costs);
  };

  return {
    recomputing,
    coverageAmounts,
    handleApplyInputs,
  };
}
