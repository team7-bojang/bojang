import { create } from 'zustand';

import type { PolicyOption } from '@/features/insurance/model';

export interface UploadedPdf {
  id: string;
  name: string;
}

interface CaseState {
  /** 홈에서 선택한 보험 상품 id. */
  selectedPolicyIds: string[];
  /** 홈에서 선택한 보험 상품 정보. */
  selectedPolicies: PolicyOption[];
  /** 홈에서 업로드한 약관 PDF. */
  uploadedPdfs: UploadedPdf[];
  setSelection: (
    selectedPolicyIds: string[],
    uploadedPdfs: UploadedPdf[],
    selectedPolicies?: PolicyOption[]
  ) => void;
}

/** 홈 → 확인 페이지로 넘기는 선택 정보 (라우트 간 공유). */
export const useCaseStore = create<CaseState>(set => ({
  selectedPolicyIds: [],
  selectedPolicies: [],
  uploadedPdfs: [],
  setSelection: (selectedPolicyIds, uploadedPdfs, selectedPolicies = []) =>
    set({ selectedPolicyIds, uploadedPdfs, selectedPolicies }),
}));
