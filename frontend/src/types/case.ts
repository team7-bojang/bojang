// 케이스/대시보드 도메인 타입.
// ⚠️ 백엔드 계약(GET /cases/{case_id}/dashboard)과 일치해야 함.

export type ServiceType = 'CASE1' | 'CASE2';

/** 챗봇 상황 입력 완료 후 확인 화면에 표시되는 9개 항목. */
export interface CaseDashboard {
  disease_name: string;
  disease_kcd: string | null;
  is_inpatient: boolean;
  is_outpatient: boolean;
  admission_days_current: number | null;
  admission_days_diagnosed: number | null;
  treatment_items: string[];
  payment_amount: number | null;
  visit_dates: string[];
  surgery: boolean;
  annual_visit_count: number | null;
  policy_elapsed_days: number | null;
}

export interface CaseDashboardResponse {
  case_id: string;
  service_type: ServiceType;
  dashboard: CaseDashboard;
}
