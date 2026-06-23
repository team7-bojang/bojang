import { endpoints } from '@/api/endpoints';
import { api } from '@/api/client';
import type { ApiEnvelope } from '@/api/types';

import type {
  MyPolicy,
  MyPolicyWithNestedPolicy,
  PolicySource,
  PolicyPresetList,
  SelectPolicyPresetsRequest,
  SelectPolicyPresetsResponse,
  UploadPolicyResponse,
} from '../model';

export async function getPolicyPresets() {
  const { data } = await api.get<ApiEnvelope<PolicyPresetList>>(endpoints.policies.presets);
  if (!data.success) {
    throw new Error(data.error.message);
  }
  return data.data;
}

export async function selectPolicyPresets(body: SelectPolicyPresetsRequest) {
  const { data } = await api.post<ApiEnvelope<SelectPolicyPresetsResponse>>(
    endpoints.policies.select,
    body
  );
  if (!data.success) {
    throw new Error(data.error.message);
  }
  return data.data;
}

export async function getMyPolicies() {
  const { data } = await api.get<ApiEnvelope<Array<MyPolicy | MyPolicyWithNestedPolicy>>>(
    endpoints.policies.my
  );
  if (!data.success) {
    throw new Error(data.error.message);
  }
  return data.data;
}

export async function uploadPolicy(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post<ApiEnvelope<UploadPolicyResponse>>(
    endpoints.policies.upload,
    formData
  );
  if (!data.success) {
    throw new Error(data.error.message);
  }
  return data.data;
}

export async function getPolicySource(policyId: string, page: number) {
  const { data } = await api.get<ApiEnvelope<PolicySource>>(endpoints.policies.source(policyId), {
    params: { page },
  });
  if (!data.success) {
    throw new Error(data.error.message);
  }
  return data.data;
}
