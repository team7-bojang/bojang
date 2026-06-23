import type { InsurerId } from '@/features/insurance/data/insurers';
import type { ServiceType } from '@/types/case';

import type {
  AnalysisCompareItem,
  AnalysisCompareResponse,
  AnalysisSearchResponse,
  AnalysisSearchResult,
} from '../model';

export type ResultLocationState = {
  analysis?: AnalysisSearchResponse | { data?: AnalysisSearchResponse };
  comparison?: AnalysisCompareResponse | { data?: AnalysisCompareResponse };
  serviceType?: ServiceType;
};

export function unwrapAnalysisFromState(state: unknown): AnalysisSearchResponse | null {
  const candidate = (state as ResultLocationState | null)?.analysis;
  if (!candidate) {
    return null;
  }
  if ('results' in candidate) {
    return candidate;
  }
  return candidate.data ?? null;
}

export function unwrapComparisonFromState(state: unknown): AnalysisCompareResponse | null {
  const candidate = (state as ResultLocationState | null)?.comparison;
  if (!candidate) {
    return null;
  }
  if ('comparison' in candidate) {
    return candidate;
  }
  return candidate.data ?? null;
}

export function isEligible(result: AnalysisSearchResult) {
  return result.status === 'eligible' && !result.missed && (result.estimated_amount ?? 0) > 0;
}

export function inferInsurerId(policy: string): InsurerId {
  if (policy.includes('KB')) {
    return 'kb';
  }
  if (policy.includes('DB')) {
    return 'db';
  }
  if (policy.includes('현대')) {
    return 'hyundai';
  }
  if (policy.includes('메리츠')) {
    return 'meritz';
  }
  if (policy.includes('한화')) {
    return 'hanwha';
  }
  if (policy.includes('교보')) {
    return 'kyobo';
  }
  return 'db';
}

export function getExpectedAmount(results: AnalysisSearchResult[]) {
  return results.reduce((sum, result) => sum + (result.estimated_amount ?? 0), 0);
}

export function getAdditionalAmount(items: AnalysisCompareItem[]) {
  return items.reduce((sum, item) => {
    const current = item.scenarios.at(0)?.estimated_amount ?? 0;
    const target = item.scenarios.at(-1)?.estimated_amount ?? 0;
    return sum + Math.max(0, target - current);
  }, 0);
}
