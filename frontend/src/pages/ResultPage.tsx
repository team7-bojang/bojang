import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard } from '@/features/case/queries';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import type { InsurerId } from '@/features/insurance/data/insurers';
import {
  compareCaseAnalysis,
  searchCaseAnalysis,
  type AnalysisCompareItem,
  type AnalysisCompareResponse,
  type AnalysisCompareScenario,
  type AnalysisSearchResponse,
  type AnalysisSearchResult,
} from '@/features/result/api/analysis';
import { AmountTiles } from '@/features/result/components/AmountTiles';
import { FireworkBurst } from '@/features/result/components/FireworkBurst';
import { formatWon } from '@/features/result/utils/format';
import { cn } from '@/lib/utils';
import type { ServiceType } from '@/types/case';

type LocationState = {
  analysis?: AnalysisSearchResponse | { data?: AnalysisSearchResponse };
  comparison?: AnalysisCompareResponse | { data?: AnalysisCompareResponse };
  serviceType?: ServiceType;
};

function unwrapAnalysisFromState(state: unknown): AnalysisSearchResponse | null {
  const candidate = (state as LocationState | null)?.analysis;
  if (!candidate) {
    return null;
  }
  if ('results' in candidate) {
    return candidate;
  }
  return candidate.data ?? null;
}

function unwrapComparisonFromState(state: unknown): AnalysisCompareResponse | null {
  const candidate = (state as LocationState | null)?.comparison;
  if (!candidate) {
    return null;
  }
  if ('comparison' in candidate) {
    return candidate;
  }
  return candidate.data ?? null;
}

function isEligible(result: AnalysisSearchResult) {
  return result.status === 'eligible' && !result.missed && (result.estimated_amount ?? 0) > 0;
}

function inferInsurerId(policy: string): InsurerId {
  if (policy.includes('KB')) {
    return 'kb';
  }
  if (policy.includes('DB')) {
    return 'db';
  }
  if (policy.includes('현대')) {
    return 'hyundai';
  }
  if (policy.includes('메리츠')) {
    return 'meritz';
  }
  if (policy.includes('한화')) {
    return 'hanwha';
  }
  if (policy.includes('교보')) {
    return 'kyobo';
  }
  return 'db';
}

function statusText(result: AnalysisSearchResult) {
  if (isEligible(result)) {
    return `${formatWon(result.estimated_amount)}원`;
  }
  if (result.status === 'not_applicable') {
    return '해당 없음';
  }
  if (result.missed) {
    return '놓친 보장';
  }
  return '조건 미달';
}

function statusTone(result: AnalysisSearchResult) {
  return isEligible(result) ? 'text-ink' : 'text-red-600';
}

function ResultRow({ result }: { result: AnalysisSearchResult }) {
  const insurerId = inferInsurerId(result.policy);

  return (
    <article className="grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:gap-5">
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{result.rider}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">{result.policy}</span>
        <span className="mt-2 line-clamp-2 block text-sm leading-6 text-muted">
          {result.explanation}
        </span>
      </span>
      <span className="text-right">
        <span className={cn('block text-lg font-black', statusTone(result))}>
          {statusText(result)}
        </span>
        <span className="mt-1 hidden text-sm font-medium text-muted sm:block">
          {result.calc ?? result.evidence?.article ?? ''}
        </span>
      </span>
    </article>
  );
}

function scenarioLabel(scenario: AnalysisCompareScenario | undefined) {
  if (!scenario) {
    return '-';
  }
  if (scenario.status === 'eligible') {
    return `${formatWon(scenario.estimated_amount)}원`;
  }
  if (scenario.status === 'boundary_not_met') {
    return '조건 미달';
  }
  if (scenario.status === 'not_applicable') {
    return '해당 없음';
  }
  return scenario.estimated_amount > 0 ? `${formatWon(scenario.estimated_amount)}원` : '조건 미달';
}

function CompareRow({ item }: { item: AnalysisCompareItem }) {
  const current = item.scenarios.at(0);
  const target = item.scenarios.at(-1);
  const additional = Math.max(
    0,
    (target?.estimated_amount ?? 0) - (current?.estimated_amount ?? 0)
  );
  const insurerId = inferInsurerId(item.policy_name);

  return (
    <article className="grid w-full grid-cols-[auto_minmax(0,1fr)] gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center sm:gap-5">
      <InsurerLogo insurerId={insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{item.rider_name}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">
          {item.policy_name}
        </span>
        <span className="mt-2 grid gap-2 text-sm font-semibold text-muted sm:grid-cols-2">
          <span>
            현재 {current?.days ?? '-'}일: {scenarioLabel(current)}
          </span>
          <span>
            목표 {target?.days ?? '-'}일: {scenarioLabel(target)}
          </span>
        </span>
        <span className="mt-2 line-clamp-2 block text-sm leading-6 text-muted">
          {target?.calc ?? current?.calc ?? ''}
        </span>
      </span>
      <span className="col-span-2 text-right sm:col-span-1">
        <span
          className={cn('block text-lg font-black', additional > 0 ? 'text-ink' : 'text-red-600')}
        >
          {additional > 0 ? `+${formatWon(additional)}원` : '추가 없음'}
        </span>
      </span>
    </article>
  );
}

function ResultHero({
  amount,
  hasPayableBenefits,
  serviceType,
}: {
  amount: number;
  hasPayableBenefits: boolean;
  serviceType: ServiceType;
}) {
  const isCompare = serviceType === 'CASE2';

  return (
    <section className="animate-result-enter relative overflow-hidden py-8 text-center sm:py-12">
      {hasPayableBenefits && (
        <>
          <FireworkBurst className="left-2 top-0 sm:left-8 sm:top-2" />
          <FireworkBurst className="right-0 top-8 sm:right-8 sm:top-10" delay={0.72} />
          <FireworkBurst className="left-20 top-24 hidden sm:block" delay={1.48} />
          <FireworkBurst className="right-24 top-28 hidden sm:block" delay={2.22} />
        </>
      )}

      <div className="relative z-10">
        <div className="font-tossface mx-auto flex size-12 items-center justify-center rounded-full bg-primary-tint text-2xl shadow-sm sm:size-14 sm:text-3xl">
          {hasPayableBenefits ? '🎉' : '🔎'}
        </div>
        <h1 className="mt-5 text-3xl font-black tracking-normal text-ink sm:text-5xl">
          분석이 완료됐어요
        </h1>
        <p className="mt-3 text-lg font-medium text-muted sm:text-2xl">
          {isCompare
            ? '입원 기간에 따라 달라지는 추가 보장을 비교했어요.'
            : hasPayableBenefits
              ? '받을 수 있는 보장을 찾았어요.'
              : '아쉽지만 바로 청구 가능한 보장은 확인하지 못했어요.'}
        </p>

        <div className="mt-10">
          <p className="mb-4 text-lg font-bold text-muted">
            {isCompare ? '추가 예상 보험금' : '예상 보험금'}
          </p>
          <AmountTiles amount={amount} />
        </div>
      </div>
    </section>
  );
}

function ResultSection({
  title,
  countClassName,
  results,
  emptyText,
  delay,
  className,
}: {
  title: string;
  countClassName: string;
  results: AnalysisSearchResult[];
  emptyText: string;
  delay: string;
  className?: string;
}) {
  return (
    <section className={cn('animate-result-enter', className)} style={{ animationDelay: delay }}>
      <h2 className="text-xl font-black text-ink">
        {title} <span className={countClassName}>{results.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {results.length > 0 ? (
          results.map((result, index) => (
            <ResultRow key={`${result.policy}-${result.rider}-${index}`} result={result} />
          ))
        ) : (
          <p className="py-6 text-sm font-semibold text-muted">{emptyText}</p>
        )}
      </div>
    </section>
  );
}

function CompareSection({ comparison }: { comparison: AnalysisCompareItem[] }) {
  return (
    <section className="animate-result-enter mt-4" style={{ animationDelay: '90ms' }}>
      <h2 className="text-xl font-black text-ink">
        추가 보장 시나리오 <span className="text-primary">{comparison.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {comparison.length > 0 ? (
          comparison.map((item, index) => (
            <CompareRow key={`${item.policy_name}-${item.rider_name}-${index}`} item={item} />
          ))
        ) : (
          <p className="py-6 text-sm font-semibold text-muted">
            추가 보장 비교 결과를 확인하지 못했습니다.
          </p>
        )}
      </div>
    </section>
  );
}

function ResultNotice({
  notice,
  serviceType,
}: {
  notice?: string | null;
  serviceType: ServiceType;
}) {
  return (
    <section className="mt-10 flex flex-col gap-4 rounded-card bg-surface/85 p-5 ring-1 ring-line sm:flex-row sm:items-center sm:justify-between">
      <p className="flex gap-3 text-sm leading-6 text-muted">
        <span className="font-tossface mt-0.5 shrink-0 text-lg">💡</span>
        <span>
          {notice ??
            (serviceType === 'CASE2'
              ? '비교 결과는 현재 입력한 입원 일수와 목표 일수를 기준으로 계산한 예상 결과입니다. 실제 지급 여부는 보험사 심사에 따라 달라질 수 있습니다.'
              : '분석 결과는 입력하신 내용과 약관 근거를 바탕으로 한 예상 결과입니다. 실제 보험금 지급 여부는 보험사 심사에 따라 달라질 수 있습니다.')}
        </span>
      </p>
      <Button type="button" variant="outline" size="lg" className="shrink-0">
        <span className="font-tossface">📄</span>
        분석 결과 리포트 다운로드
      </Button>
    </section>
  );
}

export function ResultPage() {
  const navigate = useNavigate();
  const { caseId = '' } = useParams();
  const location = useLocation();
  const stateServiceType = (location.state as LocationState | null)?.serviceType;
  const initialComparison = unwrapComparisonFromState(location.state);
  const [analysis, setAnalysis] = useState<AnalysisSearchResponse | null>(() =>
    unwrapAnalysisFromState(location.state)
  );
  const [comparison, setComparison] = useState<AnalysisCompareResponse | null>(initialComparison);
  const [serviceType, setServiceType] = useState<ServiceType>(
    stateServiceType === 'CASE2' || initialComparison ? 'CASE2' : 'CASE1'
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

    loadResult()
      .then(() => {
        if (alive) {
          setError(null);
        }
      })
      .catch(err => {
        if (alive) {
          setError(err instanceof Error ? err.message : '분석 결과를 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        if (alive) {
          setLoading(false);
        }
      });

    return () => {
      alive = false;
    };
  }, [analysis, caseId, comparison]);

  const results = useMemo(() => analysis?.results ?? [], [analysis]);
  const payableResults = useMemo(() => results.filter(isEligible), [results]);
  const nonPayableResults = useMemo(() => results.filter(result => !isEligible(result)), [results]);
  const expectedAmount = payableResults.reduce(
    (sum, result) => sum + (result.estimated_amount ?? 0),
    0
  );
  const comparisonItems = comparison?.comparison ?? [];
  const additionalAmount = comparisonItems.reduce((sum, item) => {
    const current = item.scenarios.at(0)?.estimated_amount ?? 0;
    const target = item.scenarios.at(-1)?.estimated_amount ?? 0;
    return sum + Math.max(0, target - current);
  }, 0);
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

      <main className="mx-auto w-full max-w-5xl px-5 py-8 sm:px-8">
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
                  emptyText="현재 입력 조건에서 청구 가능한 보장은 확인하지 못했습니다."
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
