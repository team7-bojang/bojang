import type { InsurerId } from './data/insurers';

export interface PolicyPreset {
  id: string;
  name: string;
  insurer: string;
  type?: string;
  is_preset?: boolean;
  created_at?: string;
}

export interface PolicyPresetList {
  presets: PolicyPreset[];
}

export interface SelectPolicyPresetsRequest {
  preset_ids: string[];
}

export interface SelectPolicyPresetsResponse {
  registered_policy_ids: string[];
}

export interface UploadPolicyResponse {
  policy_id: string;
  status: string;
}

export interface PolicySource {
  page: number;
  text: string;
}

export type VisitType = 'INPATIENT' | 'OUTPATIENT';

export interface ClaimRule {
  formula?: string;
  medical_category?: string;
  coverage_kind?: string;
  condition?: string;
  [key: string]: unknown;
}

export interface ParsePolicyRidersRequest {
  disease_kcd: string;
  disease_name?: string;
  treatment_items?: string[];
  visit_type?: VisitType;
  surgery?: boolean;
}

export interface Rider {
  id: string;
  name: string;
  is_main: boolean;
  trigger_type: string;
  trigger_detail?: string | null;
  unit_amount?: number | null;
  unit_type?: string | null;
  unit_basis?: string | null;
  boundaries?: Array<Record<string, unknown>>;
  exclusions?: string[];
  limits?: Array<Record<string, unknown>>;
  waiting_period_days?: number | null;
  reductions?: Array<Record<string, unknown>>;
  deduct_days?: number;
  claim_rule?: ClaimRule | null;
  source_pages?: number[];
  article_no?: string | null;
  page?: number | null;
  verified?: boolean;
}

export interface ParsePolicyRidersResponse {
  riders: Rider[];
}

export interface RiderSummary {
  id: string;
  name: string;
  trigger_type: string;
  unit_amount: number;
}

export interface MyPolicy {
  id: string;
  name: string;
  insurer: string;
  type?: string;
  riders: RiderSummary[];
}

export interface MyPolicyWithNestedPolicy {
  policy: Omit<MyPolicy, 'riders'>;
  riders: RiderSummary[];
}

export interface PolicyOption {
  id: string;
  insurerId: InsurerId;
  name: string;
  tags: string[];
}
