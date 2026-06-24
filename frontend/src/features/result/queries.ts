import { analysisApi } from './api';

export async function searchCaseAnalysis(caseId: string) {
  return analysisApi.searchCaseAnalysis(caseId);
}

export async function compareCaseAnalysis(caseId: string, currentDays: number, targetDays: number) {
  return analysisApi.compareCaseAnalysis(caseId, currentDays, targetDays);
}
