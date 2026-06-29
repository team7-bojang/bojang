import { apiClient, formDataClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { unwrapApiResponse } from '@/api/response';
import type { ApiResponse } from '@/api/types';

import type {
  MyPolicy,
  MyPolicyWithNestedPolicy,
  PolicyPresetList,
  PolicySource,
  SelectPolicyPresetsRequest,
  SelectPolicyPresetsResponse,
  UploadPolicyResponse,
} from './model';

export const policiesApi = {
  async getPolicyPresets() {
    const { data } = await apiClient.get<ApiResponse<PolicyPresetList>>(endpoints.policies.presets);
    return unwrapApiResponse(data);
  },

  async selectPolicyPresets(body: SelectPolicyPresetsRequest) {
    const { data } = await apiClient.post<ApiResponse<SelectPolicyPresetsResponse>>(
      endpoints.policies.select,
      body
    );
    return unwrapApiResponse(data);
  },

  async getMyPolicies() {
    const { data } = await apiClient.get<ApiResponse<Array<MyPolicy | MyPolicyWithNestedPolicy>>>(
      endpoints.policies.my
    );
    return unwrapApiResponse(data);
  },

  async uploadPolicy(file: File, onProgress?: (percent: number) => void) {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await formDataClient.post<ApiResponse<UploadPolicyResponse>>(
      endpoints.policies.upload,
      formData,
      {
        onUploadProgress: event => {
          if (onProgress && event.total) {
            onProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      }
    );
    return unwrapApiResponse(data);
  },

  async getPolicySource(policyId: string, page: number) {
    const { data } = await apiClient.get<ApiResponse<PolicySource>>(
      endpoints.policies.source(policyId),
      {
        params: { page },
      }
    );
    return unwrapApiResponse(data);
  },
};
