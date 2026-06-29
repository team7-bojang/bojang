import { apiClient, formDataClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';

import { casesApi } from './api';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
  formDataClient: {
    post: vi.fn(),
  },
}));

const mockedApi = vi.mocked(apiClient);
const mockedFormData = vi.mocked(formDataClient);

// 성공 봉투로 감싸 axios 응답 형태로 만든다
const ok = <T>(data: T) => ({ data: { success: true, data } });

beforeEach(() => {
  vi.clearAllMocks();
});

describe('casesApi 요청 경로/언래핑', () => {
  it('createCase: /cases 로 body를 보내고 data를 언래핑한다', async () => {
    const body = { service_type: 'CASE1' as const, policy_ids: ['p1'], initial_situation: '손목' };
    mockedApi.post.mockResolvedValue(ok({ case_id: 'c1' }));

    const result = await casesApi.createCase(body);

    expect(mockedApi.post).toHaveBeenCalledWith(endpoints.cases.create, body);
    expect(result).toEqual({ case_id: 'c1' });
  });

  it('saveCasePayment: caseId 기반 payment 엔드포인트로 보낸다', async () => {
    mockedApi.post.mockResolvedValue(ok({ case_id: 'c1', input_method: 'PAYMENT' }));

    await casesApi.saveCasePayment('c1', { payment_text: '8만원' });

    expect(mockedApi.post).toHaveBeenCalledWith(endpoints.cases.payment('c1'), {
      payment_text: '8만원',
    });
  });

  it('uploadMedicalDetailStatement: FormData에 file을 담아 formDataClient로 보낸다', async () => {
    mockedFormData.post.mockResolvedValue(ok({ case_id: 'c1' }));
    const file = new File(['pdf'], 'statement.pdf', { type: 'application/pdf' });

    await casesApi.uploadMedicalDetailStatement('c1', file);

    expect(mockedFormData.post).toHaveBeenCalledTimes(1);
    const [url, formData] = mockedFormData.post.mock.calls[0];
    expect(url).toBe(endpoints.cases.medicalDetailStatement('c1'));
    expect(formData).toBeInstanceOf(FormData);
    expect((formData as FormData).get('file')).toBe(file);
  });

  it('searchDiseases: q/limit/offset 파라미터와 signal을 전달한다', async () => {
    mockedApi.get.mockResolvedValue(ok({ results: [], total: 0, has_more: false, offset: 0 }));
    const controller = new AbortController();

    await casesApi.searchDiseases('손목', 5, controller.signal);

    expect(mockedApi.get).toHaveBeenCalledWith(endpoints.diseases.search, {
      params: { q: '손목', limit: 5, offset: 5 },
      signal: controller.signal,
    });
  });

  it('실패 봉투면 에러 메시지를 던진다', async () => {
    mockedApi.post.mockResolvedValue({
      data: { success: false, error: { message: '잘못된 요청' } },
    });

    await expect(
      casesApi.createCase({ service_type: 'CASE1', policy_ids: [], initial_situation: '' })
    ).rejects.toThrow('잘못된 요청');
  });
});

describe('getCaseDashboard 정규화', () => {
  it('dashboard가 비어도 기본값으로 채운다', async () => {
    mockedApi.get.mockResolvedValue(ok({ case_id: 'c1', dashboard: {} }));

    const result = await casesApi.getCaseDashboard('c1');

    expect(result.case_id).toBe('c1');
    expect(result.service_type).toBe('CASE1');
    expect(result.dashboard).toMatchObject({
      disease_name: '',
      disease_kcd: null,
      is_inpatient: false,
      is_outpatient: false,
      surgery: false,
      treatment_items: [],
      visit_dates: [],
    });
    expect(result.treatment_types).toEqual([]);
  });

  it('legacy case 페이로드(id/current_days/visit_date 단일값)를 호환 매핑한다', async () => {
    mockedApi.get.mockResolvedValue(
      ok({
        case: {
          id: 'legacy-1',
          current_days: 3,
          diag_days: 5,
          visit_date: '2026-06-10',
          disease_name: '손목터널증후군',
        },
      })
    );

    const result = await casesApi.getCaseDashboard('legacy-1');

    expect(result.case_id).toBe('legacy-1');
    expect(result.dashboard.admission_days_current).toBe(3);
    expect(result.dashboard.admission_days_diagnosed).toBe(5);
    expect(result.dashboard.visit_dates).toEqual(['2026-06-10']);
    expect(result.dashboard.disease_name).toBe('손목터널증후군');
  });

  it('visit_dates 배열에서 falsy 값을 제거한다', async () => {
    mockedApi.get.mockResolvedValue(
      ok({ case_id: 'c1', dashboard: { visit_dates: ['2026-06-10', '', '2026-06-12'] } })
    );

    const result = await casesApi.getCaseDashboard('c1');

    expect(result.dashboard.visit_dates).toEqual(['2026-06-10', '2026-06-12']);
  });
});
