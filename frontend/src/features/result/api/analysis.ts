import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ApiEnvelope } from '@/api/types';

export interface AnalysisSearchRequest {
  case_id: string;
}

export interface AnalysisCompareRequest {
  case_id: string;
  current_days: number;
  target_days: number;
}

export interface AnalysisSearchSummary {
  eligible_count: number;
  missed_count: number;
}

export interface AnalysisSearchResult {
  policy: string;
  rider: string;
  status: string;
  missed?: boolean;
  gap_days: number | null;
  payable_days: number | null;
  estimated_amount: number;
  calc: string | null;
  explanation: string;
  reduction?: unknown;
  evidence?: {
    article?: string;
    page?: number;
    quote?: string;
  } | null;
}

export interface AnalysisSearchResponse {
  notice?: string | null;
  summary: AnalysisSearchSummary;
  results: AnalysisSearchResult[];
}

export interface AnalysisCompareScenario {
  days: number;
  status: string;
  calc: string | null;
  estimated_amount: number;
}

export interface AnalysisCompareItem {
  policy_name: string;
  rider_name: string;
  scenarios: AnalysisCompareScenario[];
}

export interface AnalysisCompareResponse {
  comparison: AnalysisCompareItem[];
}

function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success) {
    throw new Error(envelope.error.message);
  }
  return envelope.data;
}

export async function searchCaseAnalysis(caseId: string) {
  const { data } = await api.post<ApiEnvelope<AnalysisSearchResponse>>(endpoints.analysis.search, {
    case_id: caseId,
  } satisfies AnalysisSearchRequest);
  return unwrap(data);
}

export async function compareCaseAnalysis(caseId: string, currentDays: number, targetDays: number) {
  const { data } = await api.post<ApiEnvelope<AnalysisCompareResponse>>(
    endpoints.analysis.compare,
    {
      case_id: caseId,
      current_days: currentDays,
      target_days: targetDays,
    } satisfies AnalysisCompareRequest
  );
  return unwrap(data);
}
