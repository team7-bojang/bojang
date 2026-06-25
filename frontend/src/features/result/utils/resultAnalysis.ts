import { INSURERS, type InsurerId } from '@/features/insurance/data/insurers';
import type { ServiceType } from '@/types/case';

import type {
  AnalysisCompareItem,
  AnalysisCompareResponse,
  AnalysisSearchResponse,
  AnalysisSearchResult,
  PayableBenefit,
} from '../model';
import { formatWon } from './format';

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

// 탐색 응답(AnalysisSearchResult)을 상세 분석 모달이 쓰는 Benefit 형태로 변환한다.
// API가 제공하지 않는 값(원문 하이라이트·결제내역 기반 설명 등)은 빈 문자열로 두고,
// 모달이 빈 값을 감지해 해당 영역을 숨긴다.
export function toPayableBenefit(result: AnalysisSearchResult): PayableBenefit {
  const insurerId = inferInsurerId(result.policy);
  const article = result.evidence?.article ?? '';
  const page = result.evidence?.page;

  // 정액 일시금이 가입금액 그대로(100%) 지급되는 경우(calc 이 금액과 동일)에는
  // 계산식을 금액 대신 '보험가입금액의 100%'로 표현한다.
  const isFullFixedPayout =
    result.estimated_amount > 0 && result.calc === `${formatWon(result.estimated_amount)}원`;
  const formula = isFullFixedPayout ? '보험가입금액의 100%' : (result.calc ?? '');

  // 판정 라벨은 상태에 맞춘다. conditional(조건 확인 필요) → '확인 필요'.
  const decision = isConditional(result)
    ? '확인 필요'
    : isEligible(result)
      ? '청구 가능'
      : '조건 미달';

  return {
    id: result.rider_id ?? `${result.policy}-${result.rider}`,
    title: result.rider,
    insurerId,
    insurerName: INSURERS[insurerId].name,
    policyName: result.policy,
    amount: result.estimated_amount ?? 0,
    analysis: {
      decision,
      decisionDescription: result.explanation,
      clauseTitle: article || result.rider,
      clausePage: page !== null && page !== undefined ? `${page}p` : '',
      clauseQuote: result.evidence?.quote ?? '',
      clauseHighlight: '',
      paymentBasis: '',
      period:
        result.payable_days !== null && result.payable_days !== undefined
          ? `${result.payable_days}일`
          : '',
      formula,
      expectedAmount: result.estimated_amount ?? 0,
      paymentCalculationDescription: '',
    },
  };
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
