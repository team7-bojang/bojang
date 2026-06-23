import type { CaseDashboard } from '@/types/case';

import {
  createCase,
  getCaseDashboard,
  patchCaseDashboard,
  saveCasePayment,
  saveCaseAnswers,
  uploadMedicalDetailStatement,
} from './api/cases';
import type { CreateCaseRequest, SaveAnswersRequest, SavePaymentRequest } from './model';

export async function startCaseAnalysis(params: CreateCaseRequest) {
  return createCase(params);
}

export async function answerCase(caseId: string, body: SaveAnswersRequest) {
  return saveCaseAnswers(caseId, body);
}

export async function submitCasePayment(caseId: string, body: SavePaymentRequest) {
  return saveCasePayment(caseId, body);
}

export async function submitMedicalDetailStatement(caseId: string, file: File) {
  return uploadMedicalDetailStatement(caseId, file);
}

export async function fetchCaseDashboard(caseId: string) {
  return getCaseDashboard(caseId);
}

export async function saveCaseDashboard(caseId: string, dashboard: CaseDashboard) {
  return patchCaseDashboard(caseId, dashboard);
}
