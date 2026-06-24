import { casesApi, type CaseDashboardPatchRequest } from './api';
import type { CreateCaseRequest, SaveAnswersRequest, SavePaymentRequest } from './model';

export async function startCaseAnalysis(params: CreateCaseRequest) {
  return casesApi.createCase(params);
}

export async function answerCase(caseId: string, body: SaveAnswersRequest) {
  return casesApi.saveCaseAnswers(caseId, body);
}

export async function submitCasePayment(caseId: string, body: SavePaymentRequest) {
  return casesApi.saveCasePayment(caseId, body);
}

export async function submitMedicalDetailStatement(caseId: string, file: File) {
  return casesApi.uploadMedicalDetailStatement(caseId, file);
}

export async function fetchCaseDashboard(caseId: string) {
  return casesApi.getCaseDashboard(caseId);
}

export async function saveCaseDashboard(caseId: string, dashboard: CaseDashboardPatchRequest) {
  return casesApi.patchCaseDashboard(caseId, dashboard);
}
