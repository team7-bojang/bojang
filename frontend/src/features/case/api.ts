import { apiClient, formDataClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { unwrapApiResponse } from '@/api/response';
import type { ApiResponse } from '@/api/types';

import type {
  CaseDashboard,
  CaseDashboardResponse,
  CreateCaseRequest,
  CreateCaseResponse,
  DiseaseSearchResponse,
  SaveAnswersRequest,
  SaveAnswersResponse,
  SaveMedicalDetailStatementResponse,
  SavePaymentRequest,
  SavePaymentResponse,
} from './model';

export type CaseDashboardPatchRequest = Partial<CaseDashboard>;

export const casesApi = {
  async createCase(body: CreateCaseRequest) {
    const { data } = await apiClient.post<ApiResponse<CreateCaseResponse>>(
      endpoints.cases.create,
      body
    );
    return unwrapApiResponse(data);
  },

  async saveCasePayment(caseId: string, body: SavePaymentRequest) {
    const { data } = await apiClient.post<ApiResponse<SavePaymentResponse>>(
      endpoints.cases.payment(caseId),
      body
    );
    return unwrapApiResponse(data);
  },

  async uploadMedicalDetailStatement(caseId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await formDataClient.post<ApiResponse<SaveMedicalDetailStatementResponse>>(
      endpoints.cases.medicalDetailStatement(caseId),
      formData
    );
    return unwrapApiResponse(data);
  },

  async saveCaseAnswers(caseId: string, body: SaveAnswersRequest) {
    const { data } = await apiClient.post<ApiResponse<SaveAnswersResponse>>(
      endpoints.cases.answers(caseId),
      body
    );
    return unwrapApiResponse(data);
  },

  async getCaseDashboard(caseId: string): Promise<CaseDashboardResponse> {
    const { data } = await apiClient.get<ApiResponse<CaseDashboardResponse>>(
      endpoints.cases.dashboard(caseId)
    );
    return normalizeDashboardResponse(unwrapApiResponse(data));
  },

  async patchCaseDashboard(caseId: string, body: CaseDashboardPatchRequest) {
    const { data } = await apiClient.patch<ApiResponse<CaseDashboardResponse>>(
      endpoints.cases.dashboard(caseId),
      body
    );
    return normalizeDashboardResponse(unwrapApiResponse(data));
  },

  async patchExtractedInfo(caseId: string, body: Record<string, unknown>) {
    const { data } = await apiClient.patch<ApiResponse<unknown>>(
      endpoints.cases.extractedInfo(caseId),
      body
    );
    return unwrapApiResponse(data);
  },

  async searchDiseases(
    q: string,
    offset = 0,
    signal?: AbortSignal
  ): Promise<DiseaseSearchResponse> {
    const { data } = await apiClient.get<ApiResponse<DiseaseSearchResponse>>(
      endpoints.diseases.search,
      {
        params: { q, limit: 5, offset },
        signal,
      }
    );
    return unwrapApiResponse(data);
  },
};

type DashboardCasePayload = Partial<CaseDashboard> & {
  id?: string;
  current_days?: number | null;
  diag_days?: number | null;
  visit_date?: string | string[] | null;
};

function normalizeDashboardResponse(
  response: CaseDashboardResponse & { case?: DashboardCasePayload }
): CaseDashboardResponse {
  const source = (response.dashboard ?? response.case ?? {}) as DashboardCasePayload;
  const dashboard = source;
  const rawVisitDates = dashboard.visit_dates ?? dashboard.visit_date ?? [];
  const visitDates = Array.isArray(rawVisitDates)
    ? rawVisitDates.filter(Boolean)
    : rawVisitDates
      ? [rawVisitDates]
      : [];

  return {
    ...response,
    case_id: response.case_id ?? response.case?.id ?? '',
    service_type: response.service_type ?? 'CASE1',
    dashboard: {
      ...dashboard,
      disease_name: dashboard.disease_name ?? '',
      disease_kcd: dashboard.disease_kcd ?? null,
      is_inpatient: dashboard.is_inpatient ?? false,
      is_outpatient: dashboard.is_outpatient ?? false,
      admission_days_current: dashboard.admission_days_current ?? dashboard.current_days ?? null,
      admission_days_diagnosed: dashboard.admission_days_diagnosed ?? dashboard.diag_days ?? null,
      surgery: dashboard.surgery ?? false,
      treatment_items: dashboard.treatment_items ?? [],
      payment_amount: dashboard.payment_amount ?? null,
      visit_dates: visitDates,
      annual_visit_count: dashboard.annual_visit_count ?? null,
      policy_elapsed_days: dashboard.policy_elapsed_days ?? null,
    },
    treatment_types: response.treatment_types ?? [],
  };
}
