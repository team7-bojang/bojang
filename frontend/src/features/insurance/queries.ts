import { INSURER_LIST, type InsurerId } from './data/insurers';
import { getMyPolicies, getPolicyPresets, selectPolicyPresets, uploadPolicy } from './api/policies';
import type { MyPolicy, MyPolicyWithNestedPolicy, PolicyOption, PolicyPreset } from './model';

const insurerAliases: Record<string, InsurerId> = {
  KB손해보험: 'kb',
  DB손해보험: 'db',
  현대해상: 'hyundai',
  현대해상화재보험: 'hyundai',
  메리츠화재: 'meritz',
  메리츠화재해상보험: 'meritz',
  한화손해보험: 'hanwha',
  한화생명: 'hanwha',
  교보생명: 'kyobo',
};

function resolveInsurerId(insurer: string): InsurerId {
  const exact = insurerAliases[insurer];
  if (exact) {
    return exact;
  }

  const partial = INSURER_LIST.find(
    item => insurer.includes(item.name) || item.name.includes(insurer)
  );
  return partial?.id ?? 'kb';
}

export function toPolicyOption(preset: PolicyPreset): PolicyOption {
  return {
    id: preset.id,
    insurerId: resolveInsurerId(preset.insurer),
    name: preset.name,
    tags: [preset.insurer, preset.type].filter(Boolean) as string[],
  };
}

export async function fetchPolicyOptions(): Promise<PolicyOption[]> {
  const { presets } = await getPolicyPresets();
  return presets.map(toPolicyOption);
}

export async function fetchMyPolicyOptions(): Promise<PolicyOption[]> {
  const policies = await getMyPolicies();
  return policies.map(policy => {
    const item = 'policy' in policy ? toFlatMyPolicy(policy) : policy;
    return {
      id: item.id,
      insurerId: resolveInsurerId(item.insurer),
      name: item.name,
      tags: [item.insurer, item.type].filter(Boolean) as string[],
    };
  });
}

export async function registerSelectedPolicyPresets(policyIds: string[]) {
  return selectPolicyPresets({ preset_ids: policyIds });
}

export async function uploadUserPolicy(file: File) {
  return uploadPolicy(file);
}

function toFlatMyPolicy(policy: MyPolicyWithNestedPolicy): MyPolicy {
  return {
    ...policy.policy,
    riders: policy.riders,
  };
}
