import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { unwrapApiResponse } from '@/api/response';
import type { ApiResponse } from '@/api/types';

import type {
  AnalysisCompareRequest,
  AnalysisCompareResponse,
  AnalysisSearchRequest,
  AnalysisSearchResponse,
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
