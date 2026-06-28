import { analysisApi } from './api';
import type { CoverageAmountInput, MedicalCostInput } from './model';

export async function searchCaseAnalysis(caseId: string) {
  return analysisApi.searchCaseAnalysis(caseId);
}

export async function judgeCaseAnalysis(
  caseId: string,
  coverageAmounts?: CoverageAmountInput[],
  medicalCosts?: MedicalCostInput
) {
  return analysisApi.judgeCaseAnalysis(caseId, coverageAmounts, medicalCosts);
}

export async function compareCaseAnalysis(caseId: string, currentDays: number, targetDays: number) {
  return analysisApi.compareCaseAnalysis(caseId, currentDays, targetDays);
}
