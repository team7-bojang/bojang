import { Stepper } from '@/components/common/Stepper';
import {
  additionalCoverageResult,
  expectedAmount,
  missingBenefits,
  payableBenefits,
} from '@/features/result/mocks/resultData';
import { Button } from '@/components/ui/button';
import { AppHeader } from '@/components/common/AppHeader';
import { AdditionalCoverageResult } from '@/features/result/components/AdditionalCoverageResult';
import { AmountTiles } from '@/features/result/components/AmountTiles';
import { AnalysisModal } from '@/features/result/components/AnalysisModal';
import { BenefitRow } from '@/features/result/components/BenefitRow';
import { FireworkBurst } from '@/features/result/components/FireworkBurst';
import type { Benefit } from '@/features/result/types';
import { cn } from '@/lib/utils';
import { Download, Info, RotateCcw, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

function ResultHero() {
  const hasPayableBenefits = payableBenefits.length > 0;

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
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-primary-tint text-primary shadow-sm sm:size-14">
          <Sparkles className="size-6 sm:size-7" />
        </div>
        <h1 className="mt-5 text-3xl font-black tracking-normal text-ink sm:text-5xl">
          분석이 완료되었어요!
        </h1>
        <p className="mt-3 text-lg font-medium text-muted sm:text-2xl">
          받을 수 있는 보장을 찾았습니다
        </p>

        <div className="mt-10">
          <p className="mb-4 text-lg font-bold text-muted">예상 보험금</p>
          <AmountTiles amount={expectedAmount} />
        </div>
      </div>
    </section>
  );
}

function BenefitSection({
  title,
  countClassName,
  benefits,
  delay,
  className,
  onSelect,
}: {
  title: string;
  countClassName: string;
  benefits: Benefit[];
  delay: string;
  className?: string;
  onSelect: (benefit: Benefit) => void;
}) {
  return (
    <section className={cn('animate-result-enter', className)} style={{ animationDelay: delay }}>
      <h2 className="text-xl font-black text-ink">
        {title} <span className={countClassName}>{benefits.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {benefits.map(benefit => (
          <BenefitRow key={benefit.id} benefit={benefit} onClick={() => onSelect(benefit)} />
        ))}
      </div>
    </section>
  );
}

function ResultNotice() {
  return (
    <section className="mt-10 flex flex-col gap-4 rounded-card bg-surface/85 p-5 ring-1 ring-line sm:flex-row sm:items-center sm:justify-between">
      <p className="flex gap-3 text-sm leading-6 text-muted">
        <Info className="mt-0.5 size-5 shrink-0 text-primary" />
        <span>
          위 결과는 입력하신 내용을 기반으로 분석된 예상 결과입니다.
          <br />
          실제 보험금 지급 여부는 보험사 심사에 따라 달라질 수 있습니다.
        </span>
      </p>
      <Button type="button" variant="outline" size="lg" className="shrink-0">
        <Download />
        분석 결과 리포트 다운로드
      </Button>
    </section>
  );
}

/** 3단계: 분석 결과. */
export function ResultPage() {
  const navigate = useNavigate();
  const { caseId = '' } = useParams();
  const { search } = useLocation();
  const [selectedBenefit, setSelectedBenefit] = useState<Benefit | null>(null);
  const normalizedCaseId = caseId.toLowerCase();
  const normalizedSearch = search.toLowerCase();
  const isAdditionalCoverageCase =
    normalizedCaseId.includes('case2') ||
    normalizedCaseId.includes('additional') ||
    normalizedSearch.includes('servicetype=case2') ||
    normalizedSearch.includes('case=2');

  useEffect(() => {
    if (!selectedBenefit) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedBenefit(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBenefit]);

  return (
    <div className="min-h-screen bg-linear-to-b from-surface via-surface to-primary-tint">
      <AppHeader />

      <div className="border-b border-line bg-surface/80">
        <div className="mx-auto max-w-5xl px-5 py-4 sm:px-8">
          <Stepper current={3} />
        </div>
      </div>

      <main className="mx-auto w-full max-w-5xl px-5 py-8 sm:px-8">
        {isAdditionalCoverageCase ? (
          <AdditionalCoverageResult
            data={additionalCoverageResult}
            onRestart={() => navigate('/home')}
          />
        ) : (
          <>
            <ResultHero />

            <BenefitSection
              title="청구 가능한 보장"
              countClassName="text-primary"
              benefits={payableBenefits}
              delay="90ms"
              className="mt-4"
              onSelect={setSelectedBenefit}
            />

            <BenefitSection
              title="조건 미달 보장"
              countClassName="text-red-600"
              benefits={missingBenefits}
              delay="160ms"
              className="mt-10"
              onSelect={setSelectedBenefit}
            />

            <ResultNotice />

            <div className="mt-8 grid gap-3 sm:mx-auto sm:max-w-2xl sm:grid-cols-2">
              <Button type="button" variant="outline" size="lg" onClick={() => navigate('/home')}>
                처음으로 돌아가기
              </Button>
              <Button type="button" size="lg" onClick={() => navigate('/home')}>
                <RotateCcw />
                새로운 상황 분석하기
              </Button>
            </div>
          </>
        )}
      </main>

      {selectedBenefit && (
        <AnalysisModal benefit={selectedBenefit} onClose={() => setSelectedBenefit(null)} />
      )}
    </div>
  );
}

export default ResultPage;
