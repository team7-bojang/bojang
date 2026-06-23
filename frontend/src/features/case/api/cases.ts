import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ApiEnvelope } from '@/api/types';

import type {
  CaseDashboard,
  CaseDashboardResponse,
  CreateCaseRequest,
  CreateCaseResponse,
  SaveAnswersRequest,
  SaveAnswersResponse,
  SaveMedicalDetailStatementResponse,
  SavePaymentRequest,
  SavePaymentResponse,
} from '../model';

function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success) {
    throw new Error(envelope.error.message);
  }
  return envelope.data;
}

export async function createCase(body: CreateCaseRequest) {
  const { data } = await api.post<ApiEnvelope<CreateCaseResponse>>(endpoints.cases.create, body);
  return unwrap(data);
}

export async function saveCasePayment(caseId: string, body: SavePaymentRequest) {
  const { data } = await api.post<ApiEnvelope<SavePaymentResponse>>(
    endpoints.cases.payment(caseId),
    body
  );
  return unwrap(data);
}

export async function uploadMedicalDetailStatement(caseId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post<ApiEnvelope<SaveMedicalDetailStatementResponse>>(
    endpoints.cases.medicalDetailStatement(caseId),
    formData
  );
  return unwrap(data);
}

export async function saveCaseAnswers(caseId: string, body: SaveAnswersRequest) {
  const { data } = await api.post<ApiEnvelope<SaveAnswersResponse>>(
    endpoints.cases.answers(caseId),
    body
  );
  return unwrap(data);
}

export async function getCaseDashboard(caseId: string): Promise<CaseDashboardResponse> {
  const { data } = await api.get<ApiEnvelope<CaseDashboardResponse>>(
    endpoints.cases.dashboard(caseId)
  );
  return normalizeDashboardResponse(unwrap(data));
}

export async function patchCaseDashboard(caseId: string, body: Partial<CaseDashboard>) {
  const { data } = await api.patch<ApiEnvelope<CaseDashboardResponse>>(
    endpoints.cases.dashboard(caseId),
    body
  );
  return normalizeDashboardResponse(unwrap(data));
}

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
  };
}
