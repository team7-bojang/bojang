import { analysisApi } from './api';
import type { CoverageAmountInput } from './model';

export async function searchCaseAnalysis(caseId: string) {
  return analysisApi.searchCaseAnalysis(caseId);
}

export async function judgeCaseAnalysis(caseId: string, coverageAmounts?: CoverageAmountInput[]) {
  return analysisApi.judgeCaseAnalysis(caseId, coverageAmounts);
}

export async function compareCaseAnalysis(caseId: string, currentDays: number, targetDays: number) {
  return analysisApi.compareCaseAnalysis(caseId, currentDays, targetDays);
}
