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
