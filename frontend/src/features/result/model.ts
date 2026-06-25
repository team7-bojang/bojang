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
  missed?: boolean;
  gap_days: number | null;
  payable_days: number | null;
  estimated_amount: number;
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

export interface AnalysisSearchResponse {
  notice?: string | null;
  summary: AnalysisSearchSummary;
  results: AnalysisSearchResult[];
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
