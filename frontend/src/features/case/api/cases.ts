import type { CaseDashboardResponse } from '@/types/case';

/**
 * 케이스 대시보드 조회 (확인 화면 prefill).
 * TODO: 백엔드 연동 시 아래 mock 대신 실제 호출 사용.
 *   const { data } = await api.get<Envelope<CaseDashboardResponse>>(`/cases/${caseId}/dashboard`);
 *   return data.data;
 */
export async function getCaseDashboard(caseId: string): Promise<CaseDashboardResponse> {
  await new Promise(resolve => setTimeout(resolve, 400));
  return {
    case_id: caseId,
    service_type: 'CASE1',
    dashboard: {
      disease_name: '허리디스크',
      disease_kcd: 'M511',
      is_inpatient: false,
      is_outpatient: true,
      admission_days_current: null,
      admission_days_diagnosed: null,
      treatment_items: ['도수치료', '물리치료'],
      payment_amount: 90000,
      visit_dates: ['2026-06-10'],
      surgery: false,
      annual_visit_count: 5,
      policy_elapsed_days: 365,
    },
  };
}
