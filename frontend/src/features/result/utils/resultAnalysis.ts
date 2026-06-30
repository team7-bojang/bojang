import { INSURERS, type InsurerId } from '@/features/insurance/data/insurers';
import type { ServiceType } from '@/types/case';

import type { CoverageGroupRow } from '../components/CoverageAmountForm';
import type {
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
  // CASE2 입원 기간 비교에 필요한 입원일수. 직전 화면(검토 폼)에서 이미 알고 있으므로 넘겨,
  // CASE2 결과 페이지가 금액 전용 대시보드를 다시 호출하지 않게 한다.
  scenarioDays?: { current: number; target: number } | null;
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

// 가입금액(정액 단가) 입력 대상 — 현재 지급(eligible)뿐 아니라 '조건 충족 시 추가 지급'이 가능한
// boundary_not_met(입원일수 미달)·waiting_period_not_met(면책기간 미경과)도 포함한다.
// 이들은 같은 정액 단가를 적용받아야 judge가 '조건 충족 시 추가' 금액(additional_amount)을 산출할 수 있다.
// (입력란은 상품 × 일당/정액 그룹 단위라, 같은 그룹의 eligible 특약과 묶여 입력 행이 늘지 않는다.)
export function needsCoverageAmount(result: AnalysisSearchResult) {
  return (
    result.status === 'eligible' ||
    result.status === 'boundary_not_met' ||
    result.status === 'waiting_period_not_met'
  );
}

// ── 입원 기간(일수) 시나리오 비교 (CASE2) ──
// 입원일수 표시 라벨('첫날' / 'N일차'). 그래프·보장 목록에서 공용으로 쓴다.
export function dayLabel(days: number) {
  return days <= 1 ? '첫날' : `${days}일차`;
}

// 입원일수로 게이팅되는 입원일당(is_daily) 특약만 비교 대상이다.
// 진단/수술/일시금(is_daily=false)은 입원일수와 무관해 시나리오 비교에서 제외한다.
export function isDailyRider(result: AnalysisSearchResult) {
  return result.is_daily === true;
}

// 현재 입원일수 기준 바로 청구 가능한 입원일당 보장.
export function isDailyClaimableNow(result: AnalysisSearchResult) {
  return isDailyRider(result) && result.status === 'eligible';
}

// 더 입원(의사 권고일수)하면 조건을 충족해 '새로' 청구 가능해지는 입원일당 보장.
// judge가 낸 boundary 미달(gap_days = 임계일수 − 현재일수)을 목표일수가 메우는지로 판단한다.
// (판정을 다시 하지 않고 judge 출력 status·gap_days만 해석한다.)
export function becomesDailyClaimableAt(
  result: AnalysisSearchResult,
  currentDays: number,
  targetDays: number
) {
  return (
    isDailyRider(result) &&
    result.status === 'boundary_not_met' &&
    result.gap_days !== null &&
    result.gap_days !== undefined &&
    targetDays >= currentDays + result.gap_days
  );
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

// 가입금액 입력 대상(needsCoverageAmount) 결과를 (보험상품 × 일당/정액) 단위로 묶는다.
// 입원일당(1일당 단가)과 진단·정액(가입금액)은 단위가 달라 따로 입력받고, 실손은 병원비 폼에서 처리하므로 제외한다.
// 반환:
//  - coverageGroups: 폼에 그릴 그룹 행(입력 순서 유지)
//  - groupRiderIds: 그룹 키 → 그 그룹에 속한 rider_id 목록(입력값을 모든 특약으로 펼쳐 재계산할 때 사용)
export function buildCoverageGroups(coverageInputResults: AnalysisSearchResult[]): {
  coverageGroups: CoverageGroupRow[];
  groupRiderIds: Record<string, string[]>;
} {
  const order: string[] = [];
  const byKey = new Map<
    string,
    {
      policy: string;
      insurerId: InsurerId;
      kind: 'daily' | 'fixed';
      riders: string[];
      riderIds: string[];
    }
  >();
  for (const result of coverageInputResults) {
    if (!result.rider_id || result.coverage_kind === '실손') {
      continue;
    }
    const kind: 'daily' | 'fixed' = result.is_daily ? 'daily' : 'fixed';
    const key = `${result.policy}|${kind}`;
    let entry = byKey.get(key);
    if (!entry) {
      entry = {
        policy: result.policy,
        insurerId: inferInsurerId(result.policy),
        kind,
        riders: [],
        riderIds: [],
      };
      byKey.set(key, entry);
      order.push(key);
    }
    if (!entry.riderIds.includes(result.rider_id)) {
      entry.riderIds.push(result.rider_id);
      entry.riders.push(result.rider);
    }
  }
  const coverageGroups: CoverageGroupRow[] = order.map(key => {
    const entry = byKey.get(key)!;
    return {
      key,
      policy: entry.policy,
      insurerId: entry.insurerId,
      kind: entry.kind,
      riders: entry.riders,
    };
  });
  const groupRiderIds: Record<string, string[]> = {};
  for (const key of order) {
    groupRiderIds[key] = byKey.get(key)!.riderIds;
  }
  return { coverageGroups, groupRiderIds };
}

export function getExpectedAmount(results: AnalysisSearchResult[]) {
  return results.reduce((sum, result) => sum + (result.estimated_amount ?? 0), 0);
}
