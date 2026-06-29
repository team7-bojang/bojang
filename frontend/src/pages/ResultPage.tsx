import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard } from '@/features/case/queries';
import { AnalysisModal } from '@/features/result/components/AnalysisModal';
import { ScenarioCompareGraph } from '@/features/result/components/ScenarioCompareGraph';
import { ClaimDocumentsSection } from '@/features/result/components/ClaimDocumentsSection';
import {
  CoverageAmountForm,
  type CoverageGroupRow,
} from '@/features/result/components/CoverageAmountForm';
import { MedicalCostForm } from '@/features/result/components/MedicalCostForm';
import { ResultHero } from '@/features/result/components/ResultHero';
import { ResultSection } from '@/features/result/components/ResultSection';
import type {
  AnalysisCompareResponse,
  AnalysisSearchResponse,
  AnalysisSearchResult,
  CoverageAmountInput,
  MedicalCostInput,
} from '@/features/result/model';
import { judgeCaseAnalysis, searchCaseAnalysis } from '@/features/result/queries';
import {
  getExpectedAmount,
  inferInsurerId,
  isConditional,
  isDailyRider,
  isEligible,
  needsCoverageAmount,
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
  const [comparison] = useState<AnalysisCompareResponse | null>(initialComparison);
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
  // 실손 covered_amount 입력값(급여 본인부담 / 비급여 의료비). 가입금액과 함께 매 재계산에 실어 보낸다.
  const [medicalCosts, setMedicalCosts] = useState<MedicalCostInput>({});
  // 시나리오 비교용 입원일수 — 현재(admission_days_current) vs 의사권고(admission_days_diagnosed).
  const [scenarioDays, setScenarioDays] = useState<{ current: number; target: number } | null>(
    null
  );

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
      const patientPaid = dashboard.dashboard.patient_paid_amount;
      const nonCovered = dashboard.dashboard.non_covered_amount;
      setMedicalCosts({
        patient_paid_amount: patientPaid !== null && patientPaid !== undefined ? patientPaid : undefined,
        non_covered_amount: nonCovered !== null && nonCovered !== undefined ? nonCovered : undefined,
      });
      // CASE1·CASE2 모두 judge 결과(case2_summary 포함)로 로드한다.
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

  // 시나리오 비교용 입원일수를 대시보드에서 로드한다.
  // 분석 결과가 navigation state 로 미리 들어오면 위 load effect 가 스킵되므로 일수는 따로 가져온다.
  useEffect(() => {
    if (!caseId) {
      return;
    }
    let alive = true;
    fetchCaseDashboard(caseId)
      .then(dashboard => {
        if (!alive) {
          return;
        }
        const current = dashboard.dashboard.admission_days_current;
        const diagnosed = dashboard.dashboard.admission_days_diagnosed;
        if (current !== null && current !== undefined) {
          setScenarioDays({ current, target: diagnosed ?? current });
        }
        const patientPaid = dashboard.dashboard.patient_paid_amount;
        const nonCovered = dashboard.dashboard.non_covered_amount;
        setMedicalCosts({
          patient_paid_amount: patientPaid !== null && patientPaid !== undefined ? patientPaid : undefined,
          non_covered_amount: nonCovered !== null && nonCovered !== undefined ? nonCovered : undefined,
        });
      })
      .catch(() => {
        // 일수 로드 실패 시 시나리오 비교는 생략하고 기존 그래프로 폴백한다.
      });
    return () => {
      alive = false;
    };
  }, [caseId]);

  const results = useMemo(() => analysis?.results ?? [], [analysis]);
  const payableResults = useMemo(() => results.filter(isEligible), [results]);
  const conditionalResults = useMemo(() => results.filter(isConditional), [results]);
  // 가입금액 입력 대상 — eligible 외에 boundary_not_met·waiting_period_not_met(조건 충족 시 추가)도 포함해
  // 같은 정액 단가를 적용받게 한다. (이게 빠지면 boundary 특약의 '조건 충족 시 추가' 금액이 0으로 누락된다.)
  const coverageInputResults = useMemo(() => results.filter(needsCoverageAmount), [results]);
  // 실손 특약이 하나라도 있으면 병원비 입력 폼을 노출한다(coverage_kind 단일 출처로 판단).
  const hasReimbursementRiders = useMemo(
    () => results.some(result => result.coverage_kind === '실손'),
    [results]
  );
  const payablePolicyNames = useMemo(
    () => [...new Set(payableResults.map(result => result.policy))],
    [payableResults]
  );
  // 청구 가능한 정액 보장을 (보험상품 × 일당/정액) 단위로 묶는다.
  // 입원일당(1일당 단가)과 진단·정액(가입금액)은 단위가 달라 따로 입력받는다. (실손은 병원비 폼에서 처리)
  const { coverageGroups, groupRiderIds } = useMemo(() => {
    const order: string[] = [];
    const byKey = new Map<
      string,
      {
        policy: string;
        insurerId: ReturnType<typeof inferInsurerId>;
        kind: 'daily' | 'fixed';
        riders: string[];
        riderIds: string[];
      }
    >();
    for (const result of coverageInputResults) {
      if (!result.rider_id || result.coverage_kind === '실손') {
        continue;
      }
      const kind: 'daily' | 'fixed' = result.is_daily ? 'daily' : 'fixed';
      const key = `${result.policy}|${kind}`;
      let entry = byKey.get(key);
      if (!entry) {
        entry = {
          policy: result.policy,
          insurerId: inferInsurerId(result.policy),
          kind,
          riders: [],
          riderIds: [],
        };
        byKey.set(key, entry);
        order.push(key);
      }
      if (!entry.riderIds.includes(result.rider_id)) {
        entry.riderIds.push(result.rider_id);
        entry.riders.push(result.rider);
      }
    }
    const rows: CoverageGroupRow[] = order.map(key => {
      const entry = byKey.get(key)!;
      return {
        key,
        policy: entry.policy,
        insurerId: entry.insurerId,
        kind: entry.kind,
        riders: entry.riders,
      };
    });
    const riderIdMap: Record<string, string[]> = {};
    for (const key of order) {
      riderIdMap[key] = byKey.get(key)!.riderIds;
    }
    return { coverageGroups: rows, groupRiderIds: riderIdMap };
  }, [coverageInputResults]);

  // 선택된 특약은 rider_id 로 보관하고 현재 results 에서 다시 찾는다.
  // 재계산으로 analysis 가 갱신되면 모달도 최신 estimated_amount·calc 를 자동 반영한다.
  const selectedResult = useMemo(
    () => results.find(result => result.rider_id === selectedRiderId) ?? null,
    [results, selectedRiderId]
  );

  // 가입금액(정액)과 병원비(실손)를 DB 저장 없이 judge API 본문으로 함께 보내 재계산한다.
  // judge 재계산은 무상태라 매 호출에 두 입력을 모두 실어야 한쪽 입력이 다른 쪽을 덮어쓰지 않는다.
  // (RAG 재탐색·extracted-info 는 거치지 않는다)
  const recompute = async (amountsByGroup: Record<string, number>, medical: MedicalCostInput) => {
    if (!caseId) {
      return;
    }
    setRecomputing(true);
    try {
      const payload: CoverageAmountInput[] = [];
      for (const [key, amount] of Object.entries(amountsByGroup)) {
        for (const rider_id of groupRiderIds[key] ?? []) {
          payload.push({ rider_id, amount, amount_source: '결과화면 입력' });
        }
      }
      const refreshed = await judgeCaseAnalysis(
        caseId,
        payload.length > 0 ? payload : undefined,
        medical
      );
      setAnalysis(refreshed);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '예상 보험금 계산에 실패했습니다.');
    } finally {
      setRecomputing(false);
    }
  };

  // 그룹(상품×일당/정액)별 입력값을 그 그룹의 모든 특약으로 펼쳐 보낸다(현재 병원비 입력 유지).
  const handleApplyAmounts = (amountsByGroup: Record<string, number>) => {
    setCoverageAmounts(amountsByGroup);
    void recompute(amountsByGroup, medicalCosts);
  };

  // 급여 본인부담·비급여 의료비를 보낸다(현재 가입금액 입력 유지).
  const handleApplyMedicalCosts = (costs: MedicalCostInput) => {
    setMedicalCosts(costs);
    void recompute(coverageAmounts, costs);
  };

  const expectedAmount = getExpectedAmount(payableResults);
  const displayExpectedAmount = hasCalculationBasis(payableResults) ? expectedAmount : null;
  // CASE2 는 금액을 다루지 않으므로(입원 기간 시나리오 비교 전용) hero 금액은 CASE1 에서만 쓴다.
  const heroAmount = serviceType === 'CASE2' ? null : displayExpectedAmount;
  const hasPayableBenefits =
    serviceType === 'CASE2' ? results.length > 0 : payableResults.length > 0 || heroAmount !== null;
  const displayError =
    error ??
    (serviceType === 'CASE2' && !analysis
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
              // CASE2 는 금액 입력·예상금액 없이 입원 기간(현재 vs 의사 권고)별 보장 변화만 보여준다.
              !results.some(isDailyRider) ? (
                <p className="mt-6 rounded-card bg-surface p-6 text-center text-sm font-semibold text-muted shadow-sm ring-1 ring-line">
                  입원 기간에 따라 달라지는 입원일당 보장이 확인되지 않았습니다.
                </p>
              ) : scenarioDays ? (
                <ScenarioCompareGraph
                  results={results}
                  currentDays={scenarioDays.current}
                  targetDays={scenarioDays.target}
                />
              ) : null
            ) : (
              <>
                <CoverageAmountForm
                  groups={coverageGroups}
                  initialAmounts={coverageAmounts}
                  expectedAmount={displayExpectedAmount}
                  submitting={recomputing}
                  onApply={handleApplyAmounts}
                  onMeasure={setPanelHeight}
                />

                {hasReimbursementRiders && (
                  <div className="mt-6">
                    <MedicalCostForm
                      initial={medicalCosts}
                      submitting={recomputing}
                      onApply={handleApplyMedicalCosts}
                    />
                  </div>
                )}

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
