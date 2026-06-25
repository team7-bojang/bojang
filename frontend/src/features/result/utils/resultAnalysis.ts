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
  // 'eligible' = 청구 가능. missed(놓친 보험금=eligible·미청구)는 청구 가능한 항목이므로 제외하지 않는다.
  // 가입금액 미입력 시 estimated_amount=0 이어도 지급 대상이므로 금액으로 거르지 않는다.
  return result.status === 'eligible';
}

// 'conditional' = 조건 확인 필요. judge는 적격으로 봤지만 약관 세부조건(초기/중증/생검 방식/특정암
// 별표)이 입력으로 확인 불가해 '청구 가능'으로 단정하지 않는 항목.
export function isConditional(result: AnalysisSearchResult) {
  return result.status === 'conditional';
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
