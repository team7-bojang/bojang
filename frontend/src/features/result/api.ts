import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { unwrapApiResponse } from '@/api/response';
import type { ApiResponse } from '@/api/types';

import type {
  AnalysisCompareRequest,
  AnalysisCompareResponse,
  AnalysisSearchRequest,
  AnalysisSearchResponse,
  CoverageAmountInput,
} from './model';

export const analysisApi = {
  async searchCaseAnalysis(caseId: string) {
    const { data } = await apiClient.post<ApiResponse<AnalysisSearchResponse>>(
      endpoints.analysis.search,
      {
        case_id: caseId,
      } satisfies AnalysisSearchRequest
    );
    return unwrapApiResponse(data);
  },

  async judgeCaseAnalysis(caseId: string, coverageAmounts?: CoverageAmountInput[]) {
    // 룰 엔진 전용 경량 판정 API (RAG/LLM/스냅샷 생략).
    // 가입금액(coverageAmounts)을 본문에 실어 DB 저장 없이 예상 보험금만 재계산한다.
    const { data } = await apiClient.post<ApiResponse<AnalysisSearchResponse>>(
      endpoints.analysis.judge,
      {
        case_id: caseId,
        ...(coverageAmounts ? { coverage_amounts: coverageAmounts } : {}),
      } satisfies AnalysisSearchRequest
    );
    return unwrapApiResponse(data);
  },

  async compareCaseAnalysis(caseId: string, currentDays: number, targetDays: number) {
    const { data } = await apiClient.post<ApiResponse<AnalysisCompareResponse>>(
      endpoints.analysis.compare,
      {
        case_id: caseId,
        current_days: currentDays,
        target_days: targetDays,
      } satisfies AnalysisCompareRequest
    );
    return unwrapApiResponse(data);
  },
};
