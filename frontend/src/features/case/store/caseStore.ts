import { create } from 'zustand';

export interface UploadedPdf {
  id: string;
  name: string;
}

interface CaseState {
  /** 홈에서 선택한 보험 상품 id. */
  selectedPolicyIds: string[];
  /** 홈에서 업로드한 약관 PDF. */
  uploadedPdfs: UploadedPdf[];
  setSelection: (selectedPolicyIds: string[], uploadedPdfs: UploadedPdf[]) => void;
}

/** 홈 → 확인 페이지로 넘기는 선택 정보 (라우트 간 공유). */
export const useCaseStore = create<CaseState>(set => ({
  selectedPolicyIds: [],
  uploadedPdfs: [],
  setSelection: (selectedPolicyIds, uploadedPdfs) => set({ selectedPolicyIds, uploadedPdfs }),
}));
