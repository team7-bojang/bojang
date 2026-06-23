import type { InsurerId } from '@/features/insurance/data/insurers';

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
