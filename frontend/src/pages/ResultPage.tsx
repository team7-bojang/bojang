import { useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { AnalysisModal } from '@/features/result/components/AnalysisModal';
import { Case1Result } from '@/features/result/components/Case1Result';
import { Case2Result } from '@/features/result/components/Case2Result';
import { ResultHero } from '@/features/result/components/ResultHero';
import { ResultSkeleton } from '@/features/result/components/ResultSkeleton';
import { useRecompute } from '@/features/result/hooks/useRecompute';
import { useResultData } from '@/features/result/hooks/useResultData';
import type { AnalysisSearchResult } from '@/features/result/model';
import {
  buildCoverageGroups,
  getExpectedAmount,
  isConditional,
  isEligible,
  needsCoverageAmount,
  toPayableBenefit,
} from '@/features/result/utils/resultAnalysis';

function hasCalculationBasis(results: AnalysisSearchResult[]) {
  return results.some(result => result.calc !== null);
}

export function ResultPage() {
  const navigate = useNavigate();
  const { caseId = '' } = useParams();
  const location = useLocation();
  const {
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
  } = useResultData(caseId, location.state);

  // 하단 고정 입력 패널 높이 — 본문이 패널에 가리지 않도록 하단 여백으로 확보한다.
  const [panelHeight, setPanelHeight] = useState(0);
  const [selectedRiderId, setSelectedRiderId] = useState<string | null>(null);

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
  const { coverageGroups, groupRiderIds } = useMemo(
    () => buildCoverageGroups(coverageInputResults),
    [coverageInputResults]
  );

  // 선택된 특약은 rider_id 로 보관하고 현재 results 에서 다시 찾는다.
  // 재계산으로 analysis 가 갱신되면 모달도 최신 estimated_amount·calc 를 자동 반영한다.
  const selectedResult = useMemo(
    () => results.find(result => result.rider_id === selectedRiderId) ?? null,
    [results, selectedRiderId]
  );

  const { recomputing, coverageAmounts, handleApplyInputs } = useRecompute({
    caseId,
    groupRiderIds,
    setAnalysis,
    setError,
    setMedicalCosts,
  });

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
  // CASE2 그래프는 대시보드의 입원일수(scenarioDays)가 있어야 그려지므로, 대시보드 로딩 동안에도 스켈레톤을 유지한다.
  // (preload 로 analysis 가 먼저 들어와 loading 이 false 여도 그래프 없이 타이틀만 뜨는 것을 막는다.)
  const showSkeleton = loading || (serviceType === 'CASE2' && dashboardLoading);

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
        {showSkeleton ? (
          <ResultSkeleton />
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
              <Case2Result
                results={results}
                scenarioDays={scenarioDays}
                onSelect={result => setSelectedRiderId(result.rider_id ?? null)}
              />
            ) : (
              <Case1Result
                coverageGroups={coverageGroups}
                coverageAmounts={coverageAmounts}
                displayExpectedAmount={displayExpectedAmount}
                recomputing={recomputing}
                onApplyInputs={handleApplyInputs}
                onMeasurePanel={setPanelHeight}
                hasReimbursementRiders={hasReimbursementRiders}
                medicalCosts={medicalCosts}
                payableResults={payableResults}
                conditionalResults={conditionalResults}
                payablePolicyNames={payablePolicyNames}
                onSelect={result => setSelectedRiderId(result.rider_id ?? null)}
              />
            )}

            <div className="mt-6 border-t border-line pt-6">
              <div className="grid gap-3 sm:mx-auto sm:max-w-2xl sm:grid-cols-2">
                <Button
                  type="button"
                  size="lg"
                  onClick={() => navigate('/analyze?serviceType=CASE1')}
                >
                  <span className="font-tossface">💸</span>새 청구가능보험 확인하기
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={() => navigate('/analyze?serviceType=CASE2')}
                >
                  <span className="font-tossface">🏥</span>새 조건별 보장 확인하기
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
        <AnalysisModal
          benefit={selectedBenefit}
          onClose={() => setSelectedRiderId(null)}
          hideCalculation={serviceType === 'CASE2'}
        />
      )}
    </div>
  );
}

export default ResultPage;
