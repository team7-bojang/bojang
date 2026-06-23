import type { CaseDashboard } from '@/types/case';

import {
  createCase,
  getCaseDashboard,
  patchCaseDashboard,
  patchExtractedInfo,
  saveCaseAnswers,
} from './api/cases';
import type { CreateCaseRequest, SaveAnswersRequest } from './model';

export async function startCaseAnalysis(params: CreateCaseRequest) {
  return createCase(params);
}

export async function answerCase(caseId: string, body: SaveAnswersRequest) {
  return saveCaseAnswers(caseId, body);
}

export async function fetchCaseDashboard(caseId: string) {
  return getCaseDashboard(caseId);
}

export async function saveCaseDashboard(caseId: string, dashboard: CaseDashboard) {
  return patchCaseDashboard(caseId, dashboard);
}

export async function saveExtractedInfo(
  caseId: string,
  dashboard: CaseDashboard,
  claimedPolicyIds: string[] = []
) {
  return patchExtractedInfo(caseId, {
    disease_name: dashboard.disease_name,
    disease_kcd: dashboard.disease_kcd,
    surgery: dashboard.surgery,
    current_days: dashboard.admission_days_current,
    diag_days: dashboard.admission_days_diagnosed,
    policy_elapsed_days: dashboard.policy_elapsed_days,
    treatment_items: dashboard.treatment_items,
    payment_amount: dashboard.payment_amount,
    claimed_policy_ids: claimedPolicyIds,
  });
}
