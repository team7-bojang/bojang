import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard } from '@/features/case/queries';
import { CompareSection } from '@/features/result/components/CompareSection';
import { ResultHero } from '@/features/result/components/ResultHero';
import { ResultNotice } from '@/features/result/components/ResultNotice';
import { ResultSection } from '@/features/result/components/ResultSection';
import type { AnalysisCompareResponse, AnalysisSearchResponse } from '@/features/result/model';
import { compareCaseAnalysis, searchCaseAnalysis } from '@/features/result/queries';
import {
  getAdditionalAmount,
  getExpectedAmount,
  isEligible,
  type ResultLocationState,
  unwrapAnalysisFromState,
  unwrapComparisonFromState,
} from '@/features/result/utils/resultAnalysis';
import type { ServiceType } from '@/types/case';

export function ResultPage() {
  const navigate = useNavigate();
  const { caseId = '' } = useParams();
  const location = useLocation();
  const state = location.state as ResultLocationState | null;
  const initialComparison = unwrapComparisonFromState(location.state);
  const [analysis, setAnalysis] = useState<AnalysisSearchResponse | null>(() =>
    unwrapAnalysisFromState(location.state)
  );
  const [comparison, setComparison] = useState<AnalysisCompareResponse | null>(initialComparison);
  const [serviceType, setServiceType] = useState<ServiceType>(
    state?.serviceType === 'CASE2' || initialComparison ? 'CASE2' : 'CASE1'
  );
  const [loading, setLoading] = useState(!analysis && !initialComparison);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (analysis || comparison || !caseId) {
      return;
    }

    let alive = true;
    const loadResult = async () => {
      const dashboard = await fetchCaseDashboard(caseId);
      if (!alive) {
        return;
      }

      setServiceType(dashboard.service_type);
      if (dashboard.service_type === 'CASE2') {
        const currentDays = dashboard.dashboard.admission_days_current ?? 0;
        const targetDays = dashboard.dashboard.admission_days_diagnosed ?? currentDays;
        const result = await compareCaseAnalysis(caseId, currentDays, targetDays);
        if (alive) {
          setComparison(result);
        }
        return;
      }

      const result = await searchCaseAnalysis(caseId);
      if (alive) {
        setAnalysis(result);
      }
    };

    const run = async () => {
      try {
        await loadResult();
        if (alive) {
          setError(null);
        }
      } catch (err) {
        if (alive) {
          setError(err instanceof Error ? err.message : '분석 결과를 불러오지 못했습니다.');
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };

    void run();

    return () => {
      alive = false;
    };
  }, [analysis, caseId, comparison]);

  const results = useMemo(() => analysis?.results ?? [], [analysis]);
  const payableResults = useMemo(() => results.filter(isEligible), [results]);
  const nonPayableResults = useMemo(() => results.filter(result => !isEligible(result)), [results]);
  const comparisonItems = comparison?.comparison ?? [];
  const expectedAmount = getExpectedAmount(payableResults);
  const additionalAmount = getAdditionalAmount(comparisonItems);
  const heroAmount = serviceType === 'CASE2' ? additionalAmount : expectedAmount;
  const hasPayableBenefits =
    serviceType === 'CASE2' ? additionalAmount > 0 : payableResults.length > 0;
  const displayError =
    error ??
    (serviceType === 'CASE2' && !comparison
      ? '비교 분석 결과가 없습니다. 입력 내용을 다시 확인해 주세요.'
      : null);

  return (
    <div className="min-h-screen bg-linear-to-b from-surface via-surface to-primary-tint">
      <AppHeader />

      <div className="border-b border-line bg-surface/80">
        <div className="mx-auto max-w-5xl px-5 py-4 sm:px-8">
          <Stepper current={3} />
        </div>
      </div>

      <main className="mx-auto w-full max-w-5xl px-5 sm:px-8 py-8">
        {loading ? (
          <div className="rounded-card bg-surface p-8 text-center shadow-sm ring-1 ring-line">
            <p className="text-sm font-semibold text-muted">분석 결과를 불러오고 있습니다.</p>
          </div>
        ) : displayError ? (
          <div className="rounded-card bg-surface p-8 text-center shadow-sm ring-1 ring-line">
            <span className="font-tossface text-3xl">⚠️</span>
            <p className="mt-3 text-sm font-semibold text-red-700">{displayError}</p>
            <Button
              className="mt-5"
              type="button"
              onClick={() => navigate(`/cases/${caseId}/confirm`)}
            >
              입력 내용 다시 확인
            </Button>
          </div>
        ) : (
          <>
            <ResultHero
              amount={heroAmount}
              hasPayableBenefits={hasPayableBenefits}
              serviceType={serviceType}
            />

            {serviceType === 'CASE2' ? (
              <CompareSection comparison={comparisonItems} />
            ) : (
              <>
                <ResultSection
                  title="청구 가능한 보장"
                  countClassName="text-primary"
                  results={payableResults}
                  emptyText="현재 입력 조건에서 청구 가능한 보장은 확인되지 않았습니다."
                  delay="90ms"
                  className="mt-4"
                />

                <ResultSection
                  title="조건 미달 보장"
                  countClassName="text-red-600"
                  results={nonPayableResults}
                  emptyText="조건 미달 또는 해당 없음으로 분류된 보장이 없습니다."
                  delay="160ms"
                  className="mt-10"
                />
              </>
            )}

            <ResultNotice notice={analysis?.notice} serviceType={serviceType} />

            <div className="mt-8 grid gap-3 sm:mx-auto sm:max-w-2xl sm:grid-cols-2">
              <Button type="button" variant="outline" size="lg" onClick={() => navigate('/home')}>
                처음으로 돌아가기
              </Button>
              <Button type="button" size="lg" onClick={() => navigate('/home')}>
                <span className="font-tossface">📝</span>
                새로운 상황 분석하기
              </Button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default ResultPage;
