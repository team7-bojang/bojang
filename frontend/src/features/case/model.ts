import type {
  CaseDashboard,
  CaseDashboardResponse,
  ServiceType,
  TreatmentType,
} from '@/types/case';

export type { CaseDashboard, CaseDashboardResponse, ServiceType };

export interface DiseaseCandidate {
  kcd?: string;
  code?: string;
  name: string;
  friendly_name?: string;
}

export type QuestionInputType =
  | 'radio_button'
  | 'select_button'
  | 'checkbox_button'
  | 'text_input'
  | 'file_upload';

// 백엔드 raw 옵션: 질병은 {kcd,name}, 그 외는 {value,label}(value는 boolean 가능)
export type RawQuestionOption =
  | { kcd: string; name: string }
  | { value: string | boolean; label: string };

export interface NextQuestion {
  question_id: string;
  question_text: string;
  input_type: QuestionInputType;
  placeholder?: string;
  options?: RawQuestionOption[];
  treatment_types?: TreatmentType[];
}

// 프론트 내부 정규화 형태
export interface NormalizedOption {
  value: string | boolean;
  label: string;
}

// /answers 로 전송하는 값 (단일/불리언/다중)
export type AnswerValue = string | boolean | File | Array<string | boolean>;

export interface CaseQuestion {
  index: number;
  type: string;
  text: string;
}

export interface CreateCaseRequest {
  service_type: ServiceType;
  policy_ids: string[];
  initial_situation: string;
}

export interface CreateCaseResponse {
  case_id: string | null;
  service_type?: ServiceType;
  policy_ids?: string[];
  initial_situation?: string;
  claim_status?: 'BEFORE_CLAIM' | 'AFTER_CLAIM' | 'UNKNOWN';
  claimed_policy_ids?: string[] | null;
  disease_name?: string | null;
  disease_kcd?: string | null;
  disease_candidates?: DiseaseCandidate[];
  disease_kcd_candidates?: DiseaseCandidate[];
  disease_match_confidence?: string;
  questions?: CaseQuestion[];
  recommended_input_method?: 'PAYMENT' | 'MEDICAL_DETAIL_STATEMENT' | null;
  available_input_methods?: string[];
  message?: string | null;
  next_question?: NextQuestion | null;
  treatment_types?: TreatmentType[] | null;
}

export interface SavePaymentRequest {
  input_method?: 'PAYMENT';
  payment_text: string;
}

export interface SavePaymentResponse {
  case_id: string;
  input_method: 'PAYMENT';
  next_question?: NextQuestion | null;
  extracted_payment: {
    payment_amount: number;
    payment_date: string;
    hospital_name: string;
  };
  needs_confirmation: boolean;
  visit_type_inference: {
    inferred: boolean;
    inferred_is_inpatient: boolean | null;
    inferred_is_outpatient: boolean | null;
    message: string | null;
    threshold_basis: string | null;
  };
  treatment_types?: TreatmentType[] | null;
}

export interface SaveMedicalDetailStatementResponse {
  case_id?: string;
  input_method?: 'MEDICAL_DETAIL_STATEMENT';
  extracted_medical_info?: Record<string, unknown>;
  extracted_treatments?: string[];
  covered_amounts?: Record<string, number>;
  needs_confirmation?: boolean;
  next_question?: NextQuestion | null;
  treatment_types?: TreatmentType[] | null;
}

export interface SaveAnswersRequest {
  answers: Array<{
    question_id?: string;
    question_type?: string;
    value: unknown;
  }>;
}

export interface SaveAnswersResponse {
  saved?: boolean;
  ready_for_dashboard?: boolean;
  case_id?: string;
  next_question?: NextQuestion | null;
  treatment_types?: TreatmentType[] | null;
}
