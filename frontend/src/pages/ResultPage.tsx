import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard } from '@/features/case/queries';
import { AnalysisModal } from '@/features/result/components/AnalysisModal';
import { ClaimDocumentsSection } from '@/features/result/components/ClaimDocumentsSection';
import { CompareSection } from '@/features/result/components/CompareSection';
import {
  CoverageAmountForm,
  type CoveragePolicyRow,
} from '@/features/result/components/CoverageAmountForm';
import { ResultHero } from '@/features/result/components/ResultHero';
import { ResultSection } from '@/features/result/components/ResultSection';
import type {
  AnalysisCompareResponse,
  AnalysisSearchResponse,
  AnalysisSearchResult,
  CoverageAmountInput,
} from '@/features/result/model';
import {
  compareCaseAnalysis,
  judgeCaseAnalysis,
  searchCaseAnalysis,
} from '@/features/result/queries';
import {
  getAdditionalAmount,
  getExpectedAmount,
  inferInsurerId,
  isConditional,
  isEligible,
  type ResultLocationState,
  toPayableBenefit,
  unwrapAnalysisFromState,
  unwrapComparisonFromState,
} from '@/features/result/utils/resultAnalysis';
import type { ServiceType } from '@/types/case';

function hasCalculationBasis(results: AnalysisSearchResult[]) {
  return results.some(result => result.calc !== null);
}

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
  const [recomputing, setRecomputing] = useState(false);
  // 하단 고정 입력 패널 높이 — 본문이 패널에 가리지 않도록 하단 여백으로 확보한다.
  const [panelHeight, setPanelHeight] = useState(0);
  const [selectedRiderId, setSelectedRiderId] = useState<string | null>(null);
  // 특약별 입력한 가입금액(riderId → amount). 입력값을 누적해 전체 합계·다른 특약 금액을 유지한다.
  const [coverageAmounts, setCoverageAmounts] = useState<Record<string, number>>({});

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
  const conditionalResults = useMemo(() => results.filter(isConditional), [results]);
  const payablePolicyNames = useMemo(
    () => [...new Set(payableResults.map(result => result.policy))],
    [payableResults]
  );
  // 청구 가능한 정액 보장을 보험상품(policy) 단위로 묶는다.
  // 같은 상품의 특약은 가입금액이 동일하므로 상품당 1개만 입력받고, 그 상품의 모든 특약에 적용한다.
  const { coveragePolicies, policyRiderIds } = useMemo(() => {
    const order: string[] = [];
    const byPolicy = new Map<
      string,
      { insurerId: ReturnType<typeof inferInsurerId>; riders: string[]; riderIds: string[] }
    >();
    for (const result of payableResults) {
      if (!result.rider_id) {
        continue;
      }
      let entry = byPolicy.get(result.policy);
      if (!entry) {
        entry = { insurerId: inferInsurerId(result.policy), riders: [], riderIds: [] };
        byPolicy.set(result.policy, entry);
        order.push(result.policy);
      }
      if (!entry.riderIds.includes(result.rider_id)) {
        entry.riderIds.push(result.rider_id);
        entry.riders.push(result.rider);
      }
    }
    const rows: CoveragePolicyRow[] = order.map(policy => {
      const entry = byPolicy.get(policy)!;
      return { policy, insurerId: entry.insurerId, riders: entry.riders };
    });
    const riderIdMap: Record<string, string[]> = {};
    for (const policy of order) {
      riderIdMap[policy] = byPolicy.get(policy)!.riderIds;
    }
    return { coveragePolicies: rows, policyRiderIds: riderIdMap };
  }, [payableResults]);

  // 선택된 특약은 rider_id 로 보관하고 현재 results 에서 다시 찾는다.
  // 재계산으로 analysis 가 갱신되면 모달도 최신 estimated_amount·calc 를 자동 반영한다.
  const selectedResult = useMemo(
    () => results.find(result => result.rider_id === selectedRiderId) ?? null,
    [results, selectedRiderId]
  );

  // 보험상품별로 입력받은 가입금액을 그 상품의 모든 특약(rider_id)으로 펼쳐 한 번에 judge 로 보낸다.
  // (DB 저장 없이 judge API 본문으로 직접 전달 — RAG 재탐색·extracted-info 는 거치지 않는다)
  const handleApplyAmounts = async (amountsByPolicy: Record<string, number>) => {
    if (!caseId) {
      return;
    }
    setCoverageAmounts(amountsByPolicy);
    setRecomputing(true);
    try {
      const payload: CoverageAmountInput[] = [];
      for (const [policy, amount] of Object.entries(amountsByPolicy)) {
        for (const rider_id of policyRiderIds[policy] ?? []) {
          payload.push({ rider_id, amount, amount_source: '결과화면 입력' });
        }
      }
      const refreshed = await judgeCaseAnalysis(caseId, payload);
      setAnalysis(refreshed);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '예상 보험금 계산에 실패했습니다.');
    } finally {
      setRecomputing(false);
    }
  };

  const comparisonItems = comparison?.comparison ?? [];
  const expectedAmount = getExpectedAmount(payableResults);
  const displayExpectedAmount = hasCalculationBasis(payableResults) ? expectedAmount : null;
  const additionalAmount = getAdditionalAmount(comparisonItems);
  const heroAmount = serviceType === 'CASE2' ? additionalAmount : displayExpectedAmount;
  const hasPayableBenefits =
    serviceType === 'CASE2'
      ? additionalAmount > 0
      : payableResults.length > 0 || heroAmount !== null;
  const displayError =
    error ??
    (serviceType === 'CASE2' && !comparison
      ? '비교 분석 결과가 없습니다. 입력 내용을 다시 확인해 주세요.'
      : null);
  const selectedBenefit = selectedResult ? toPayableBenefit(selectedResult) : null;

  return (
    <div className="min-h-screen bg-linear-to-b from-surface via-surface to-primary-tint">
      <AppHeader />

      <div className="border-b border-line bg-surface/80">
        <div className="mx-auto max-w-5xl px-5 py-4 sm:px-8">
          <Stepper current={3} />
        </div>
      </div>

      <main
        className="mx-auto w-full max-w-5xl px-5 py-8 sm:px-8"
        style={{ paddingBottom: panelHeight ? panelHeight + 24 : undefined }}
      >
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
              payableCount={payableResults.length}
              hasPayableBenefits={hasPayableBenefits}
              serviceType={serviceType}
            />

            {serviceType === 'CASE2' ? (
              <CompareSection comparison={comparisonItems} />
            ) : (
              <>
                <CoverageAmountForm
                  policies={coveragePolicies}
                  initialAmounts={coverageAmounts}
                  expectedAmount={displayExpectedAmount}
                  submitting={recomputing}
                  onApply={handleApplyAmounts}
                  onMeasure={setPanelHeight}
                />

                <div className="mt-6 border-t border-line pt-6">
                  <ResultSection
                    title="청구 가능한 보장"
                    countClassName="text-primary"
                    results={payableResults}
                    emptyText="현재 입력 조건에서 청구 가능한 보장은 확인되지 않았습니다."
                    delay="90ms"
                    onSelect={result => setSelectedRiderId(result.rider_id ?? null)}
                  />
                </div>

                {conditionalResults.length > 0 && (
                  <div className="mt-6 border-t border-line pt-6">
                    <ResultSection
                      title="조건 확인 필요"
                      countClassName="text-amber-600"
                      results={conditionalResults}
                      emptyText="조건 확인이 필요한 보장이 없습니다."
                      delay="125ms"
                      collapsible
                      defaultOpen={false}
                      onSelect={result => setSelectedRiderId(result.rider_id ?? null)}
                    />
                  </div>
                )}

                <div className="mt-6 border-t border-line pt-6">
                  <ClaimDocumentsSection policyNames={payablePolicyNames} />
                </div>
              </>
            )}

            <div className="mt-6 border-t border-line pt-6">
              <div className="grid gap-3 sm:mx-auto sm:max-w-2xl sm:grid-cols-2">
                <Button type="button" variant="outline" size="lg">
                  <span className="font-tossface">📄</span>
                  결과 다운로드
                </Button>
                <Button type="button" size="lg" onClick={() => navigate('/home')}>
                  <span className="font-tossface">📝</span>
                  새로운 분석
                </Button>
              </div>
              {analysis?.notice && (
                <p className="mx-auto mt-4 max-w-2xl text-center text-xs font-semibold leading-5 text-muted">
                  {analysis.notice}
                </p>
              )}
              {!analysis?.notice && (
                <p className="mx-auto mt-4 max-w-2xl text-center text-xs font-semibold leading-5 text-muted">
                  분석 결과는 입력하신 내용과 약관 근거를 바탕으로 한 예상 결과입니다. 실제 보험금
                  지급 여부는 보험사 심사에 따라 달라질 수 있습니다.
                </p>
              )}
            </div>
          </>
        )}
      </main>

      {selectedBenefit && (
        <AnalysisModal benefit={selectedBenefit} onClose={() => setSelectedRiderId(null)} />
      )}
    </div>
  );
}

export default ResultPage;
