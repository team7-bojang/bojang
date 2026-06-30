import { useEffect, useRef, useState } from 'react';

import { fetchCaseDashboard } from '@/features/case/queries';
import { searchCaseAnalysis } from '@/features/result/queries';
import type { ServiceType } from '@/types/case';

import type { AnalysisSearchResponse, MedicalCostInput } from '../model';
import {
  unwrapAnalysisFromState,
  unwrapComparisonFromState,
  type ResultLocationState,
} from '../utils/resultAnalysis';

type CaseDashboard = Awaited<ReturnType<typeof fetchCaseDashboard>>['dashboard'];

// 대시보드의 결제 금액(급여 본인부담 / 비급여)을 폼 입력값(MedicalCostInput)으로 정규화한다.
// null·undefined 는 '미입력'으로 보고 undefined 로 통일한다.
function toMedicalCosts(dashboard: CaseDashboard): MedicalCostInput {
  const patientPaid = dashboard.patient_paid_amount;
  const nonCovered = dashboard.non_covered_amount;
  return {
    patient_paid_amount:
      patientPaid !== null && patientPaid !== undefined ? patientPaid : undefined,
    non_covered_amount: nonCovered !== null && nonCovered !== undefined ? nonCovered : undefined,
  };
}

export type UseResultDataReturn = {
  analysis: AnalysisSearchResponse | null;
  setAnalysis: React.Dispatch<React.SetStateAction<AnalysisSearchResponse | null>>;
  serviceType: ServiceType;
  loading: boolean;
  /** 입원일수(scenarioDays)·병원비 기본값을 채우는 대시보드 로딩 상태. preload 여부와 무관하게 fetch 동안 true. */
  dashboardLoading: boolean;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  medicalCosts: MedicalCostInput;
  setMedicalCosts: React.Dispatch<React.SetStateAction<MedicalCostInput>>;
  scenarioDays: { current: number; target: number } | null;
};

// 결과 페이지 초기 로딩을 담당한다.
// - navigation state 로 분석/비교 결과가 미리 들어오면(preloaded) 재탐색(searchCaseAnalysis) 없이 그대로 쓴다.
// - 시나리오 입원일수·병원비 입력 기본값은 preload 여부와 무관하게 항상 대시보드에서 채운다.
//   (preload 시에도 입원일수가 필요하므로 대시보드는 한 번 호출한다.)
export function useResultData(caseId: string, locationState: unknown): UseResultDataReturn {
  const initialComparison = unwrapComparisonFromState(locationState);
  const initialAnalysis = unwrapAnalysisFromState(locationState);
  const state = locationState as ResultLocationState | null;
  const initialScenarioDays = state?.scenarioDays ?? null;
  const initialIsCase2 = state?.serviceType === 'CASE2' || !!initialComparison;

  const [analysis, setAnalysis] = useState<AnalysisSearchResponse | null>(initialAnalysis);
  const [serviceType, setServiceType] = useState<ServiceType>(initialIsCase2 ? 'CASE2' : 'CASE1');
  const [loading, setLoading] = useState(!initialAnalysis && !initialComparison);
  // 대시보드(입원일수·병원비) 로딩은 preload 여부와 무관하게 항상 fetch 하므로 true 로 시작한다.
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [medicalCosts, setMedicalCosts] = useState<MedicalCostInput>({});
  const [scenarioDays, setScenarioDays] = useState<{ current: number; target: number } | null>(
    initialScenarioDays
  );

  // preload 여부는 최초 mount 시점 값으로 고정한다(이후 setAnalysis 로 갱신돼도 재탐색하지 않도록).
  const preloadedRef = useRef(!!initialAnalysis || !!initialComparison);
  // CASE2 는 금액(병원비)을 쓰지 않으므로, preload + 입원일수가 state 로 들어오면 대시보드를 호출하지 않는다.
  const skipDashboardRef = useRef(
    (!!initialAnalysis || !!initialComparison) && initialIsCase2 && !!initialScenarioDays
  );

  useEffect(() => {
    if (!caseId) {
      return;
    }
    // 대시보드가 불필요한 CASE2(입원일수·분석 결과 모두 확보)는 fetch 없이 로딩만 종료한다.
    if (skipDashboardRef.current) {
      setLoading(false);
      setDashboardLoading(false);
      return;
    }
    let alive = true;
    const preloaded = preloadedRef.current;

    const run = async () => {
      try {
        const dashboard = await fetchCaseDashboard(caseId);
        if (!alive) {
          return;
        }

        // 입원일수·병원비 기본값은 preload 여부와 무관하게 항상 채운다.
        const current = dashboard.dashboard.admission_days_current;
        const diagnosed = dashboard.dashboard.admission_days_diagnosed;
        if (current !== null && current !== undefined) {
          setScenarioDays({ current, target: diagnosed ?? current });
        }
        setMedicalCosts(toMedicalCosts(dashboard.dashboard));

        // navigation state 로 결과가 미리 들어오지 않은 경우에만 재탐색한다.
        if (!preloaded) {
          setServiceType(dashboard.service_type);
          // CASE1·CASE2 모두 judge 결과(case2_summary 포함)로 로드한다.
          const result = await searchCaseAnalysis(caseId);
          if (!alive) {
            return;
          }
          setAnalysis(result);
        }
        setError(null);
      } catch (err) {
        // preload 된 경우(이미 보여줄 결과가 있음)에는 입원일수 로드 실패를 조용히 무시하고 폴백한다.
        if (alive && !preloaded) {
          setError(err instanceof Error ? err.message : '분석 결과를 불러오지 못했습니다.');
        }
      } finally {
        if (alive) {
          setLoading(false);
          setDashboardLoading(false);
        }
      }
    };

    void run();

    return () => {
      alive = false;
    };
  }, [caseId]);

  return {
    analysis,
    setAnalysis,
    serviceType,
    loading,
    dashboardLoading,
    error,
    setError,
    medicalCosts,
    setMedicalCosts,
    scenarioDays,
  };
}
