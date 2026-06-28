import type { InsurerId } from '@/features/insurance/data/insurers';

export interface CoverageAmountInput {
  rider_id: string;
  amount: number;
  amount_source?: string;
}

export interface AnalysisSearchRequest {
  case_id: string;
  // judge 재계산 전용: 가입금액을 DB 저장 없이 본문으로 전달해 예상 보험금을 재산출한다.
  coverage_amounts?: CoverageAmountInput[];
  // 실손 covered_amount 직접 입력 (judge 재계산 전용, DB 미저장).
  // 급여 실손 → patient_paid_amount, 비급여 실손 → non_covered_amount.
  patient_paid_amount?: number;
  non_covered_amount?: number;
}

/** 실손 covered_amount 입력값 (급여 본인부담 / 비급여 의료비). */
export interface MedicalCostInput {
  patient_paid_amount?: number;
  non_covered_amount?: number;
}

export interface AnalysisCompareRequest {
  case_id: string;
  current_days: number;
  target_days: number;
}

export interface AnalysisSearchSummary {
  eligible_count: number;
  missed_count: number;
  conditional_count?: number;
}

export interface AnalysisSearchResult {
  policy: string;
  rider: string;
  rider_id?: string;
  status: string;
  // 정액/실손 구분 (실손 병원비 입력폼 노출 분기에 사용)
  coverage_kind?: string;
  // true=입원일당(1일당 단가 입력) / false=진단·정액(가입금액 입력)
  is_daily?: boolean;
  missed?: boolean;
  gap_days: number | null;
  payable_days: number | null;
  estimated_amount: number; // 현재 받을 수 있는 (감액 반영 후)
  additional_amount?: number; // 조건 충족 시 추가로 받을 수 있는
  reduced_amount?: number; // 감액으로 못 받는 금액
  calc: string | null;
  explanation: string;
  condition?: string | null;
  reduction?: unknown;
  evidence?: {
    article?: string;
    page?: number;
    quote?: string;
  } | null;
}

/** CASE2(추가 보장·감액) 막대그래프 집계 — judge 결과 기반(백엔드 산출). */
export interface Case2SummaryItem {
  rider: string;
  policy: string;
  amount: number;
  condition?: string | null;
  reason?: string | null;
}

export interface Case2Summary {
  current_total: number; // 현재 받을 수 있는 합계
  additional_total: number; // 조건 충족 시 추가 합계
  potential_total: number; // current + additional (CASE 2-1 우측 막대)
  reduced_total: number; // 감액 합계
  before_reduction_total: number; // current + reduced (CASE 2-2 좌측 막대)
  additional_items: Case2SummaryItem[];
  reduced_items: Case2SummaryItem[];
}

export interface AnalysisSearchResponse {
  notice?: string | null;
  summary: AnalysisSearchSummary;
  results: AnalysisSearchResult[];
  case2_summary?: Case2Summary;
}

export interface AnalysisCompareScenario {
  days: number;
  status: string;
  calc: string | null;
  estimated_amount: number;
}

export interface AnalysisCompareItem {
  policy_name: string;
  rider_name: string;
  scenarios: AnalysisCompareScenario[];
}

export interface AnalysisCompareResponse {
  comparison: AnalysisCompareItem[];
}

export interface BenefitAnalysis {
  decision: '청구 가능' | '조건 미달' | '확인 필요';
  decisionDescription: string;
  clauseTitle: string;
  clausePage: string;
  clauseQuote: string;
  clauseHighlight: string;
  paymentBasis: string;
  period: string;
  formula: string;
  expectedAmount: number;
  paymentCalculationDescription: string;
}

export interface PayableBenefit {
  id: string;
  title: string;
  insurerId: InsurerId;
  insurerName: string;
  policyName: string;
  amount: number;
  analysis: BenefitAnalysis;
}

export interface MissingBenefit {
  id: string;
  title: string;
  insurerId: InsurerId;
  insurerName: string;
  policyName: string;
  reason: string;
  condition: string;
  analysis: BenefitAnalysis;
}

export type Benefit = PayableBenefit | MissingBenefit;

export interface AdditionalCoverageCandidate {
  id: string;
  title: string;
  insurerId: InsurerId;
  insurerName: string;
  policyName: string;
  potentialAmount: number;
  condition: string;
}

export interface AdditionalCoverageResultData {
  currentAmount: number;
  expectedAmount: number;
  explanation: string;
  candidates: AdditionalCoverageCandidate[];
}
