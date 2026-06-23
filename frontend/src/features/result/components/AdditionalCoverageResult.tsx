import { Button } from '@/components/ui/button';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { cn } from '@/lib/utils';
import { ChevronRight, Download, Lightbulb, RotateCcw, Sparkles } from 'lucide-react';

import type { AdditionalCoverageCandidate, AdditionalCoverageResultData } from '../types';
import { formatWon } from '../utils/format';

function AmountLabel({
  label,
  amount,
  className,
}: {
  label: string;
  amount: number;
  className?: string;
}) {
  return (
    <div className={cn('text-center', className)}>
      <p className="text-sm font-black text-muted sm:text-base">{label}</p>
      <p className="mt-2 text-3xl font-black tabular-nums text-ink sm:text-4xl">
        {formatWon(amount)}
        <span className="ml-1 text-base font-black">원</span>
      </p>
    </div>
  );
}

function CoverageGrowthChart({ data }: { data: AdditionalCoverageResultData }) {
  const additionalAmount = data.expectedAmount - data.currentAmount;
  const currentRatio = (data.currentAmount / data.expectedAmount) * 100;
  const additionalRatio = 100 - currentRatio;

  return (
    <section className="animate-result-enter pt-8 sm:pt-12">
      <div className="flex items-start gap-4">
        <div className="mt-1 text-primary">
          <Sparkles className="size-8 fill-primary/10 sm:size-10" />
        </div>
        <div>
          <h1 className="text-3xl font-black tracking-normal text-ink sm:text-5xl">
            추가로 받을 수 있는 보장을 찾았습니다
          </h1>
          <p className="mt-3 text-lg font-bold text-muted sm:text-xl">
            조건을 채우면 더 받을 수도 있어요
          </p>
        </div>
      </div>

      <div className="mt-10 rounded-card bg-surface/90 p-5 shadow-sm ring-1 ring-line sm:p-8">
        <div className="mx-auto max-w-3xl">
          <dl className="mx-auto grid max-w-2xl gap-4 rounded-card bg-canvas/70 p-5 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
            <div>
              <dt className="text-sm font-black text-primary">추가로 받을 수 있는 보험금</dt>
              <dd className="mt-1 text-2xl font-black tabular-nums text-primary">
                {formatWon(additionalAmount)}원
              </dd>
            </div>
            <div className="hidden h-12 w-px bg-line sm:block" />
            <div className="sm:text-right">
              <dt className="text-sm font-black text-muted">현재 받을 수 있는 보험금</dt>
              <dd className="mt-1 text-xl font-black tabular-nums text-ink">
                {formatWon(data.currentAmount)}원
              </dd>
            </div>
          </dl>

          <div className="mt-10 grid gap-10 sm:grid-cols-2 sm:items-end sm:gap-14">
            <div>
              <AmountLabel label="현재 받을 수 있는 보험금" amount={data.currentAmount} />
              <div className="mx-auto mt-8 h-32 w-36 overflow-hidden rounded-t-xl sm:h-44 sm:w-40">
                <div className="animate-coverage-bar-rise h-full rounded-t-xl bg-[#bfe5df]">
                  <span className="sr-only">현재 보험금 {formatWon(data.currentAmount)}원</span>
                </div>
              </div>
            </div>
            <div>
              <AmountLabel
                label="조건 충족 시 예상 보험금"
                amount={data.expectedAmount}
                className="[&_p:last-child]:text-primary"
              />
              <div className="mx-auto mt-8 h-56 w-40 overflow-hidden rounded-t-xl sm:h-72 sm:w-44">
                <div className="animate-coverage-bar-rise flex h-full flex-col">
                  <div
                    className="bg-[#18c9b5]"
                    style={{ height: `${additionalRatio}%`, minHeight: '2.5rem' }}
                  />
                  <div
                    className="bg-[#bfe5df]"
                    style={{ height: `${currentRatio}%`, minHeight: '3rem' }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function AdditionalCoverageNotice({ explanation }: { explanation: string }) {
  return (
    <section className="animate-result-enter mt-6 rounded-card bg-primary-tint/55 p-5 ring-1 ring-primary/10">
      <div className="flex gap-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface text-primary shadow-sm">
          <Lightbulb className="size-5" />
        </div>
        <div>
          <h2 className="text-base font-black text-ink">왜 더 받을 수 있나요?</h2>
          <p className="mt-2 text-sm font-semibold leading-6 text-muted">{explanation}</p>
        </div>
      </div>
    </section>
  );
}

function AdditionalCoverageRow({ candidate }: { candidate: AdditionalCoverageCandidate }) {
  return (
    <button
      type="button"
      className="grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-line/80 py-5 text-left last:border-b-0 sm:gap-5"
    >
      <InsurerLogo insurerId={candidate.insurerId} size="lg" className="rounded-full" />
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{candidate.title}</span>
        <span className="mt-1 block truncate text-sm font-medium text-muted">
          {candidate.insurerName} <span className="mx-2 text-line">|</span> {candidate.policyName}
        </span>
      </span>
      <span className="flex items-center gap-3">
        <span className="text-right">
          <span className="block text-lg font-black tabular-nums text-primary sm:text-xl">
            +{formatWon(candidate.potentialAmount)}원 가능
          </span>
          <span className="mt-1 hidden text-sm font-medium text-muted sm:block">
            조건: {candidate.condition}
          </span>
        </span>
        <ChevronRight className="size-5 shrink-0 text-muted" />
      </span>
    </button>
  );
}

function AdditionalCoverageList({ candidates }: { candidates: AdditionalCoverageCandidate[] }) {
  return (
    <section className="animate-result-enter mt-8" style={{ animationDelay: '120ms' }}>
      <h2 className="text-xl font-black text-ink">
        추가 보장 가능성 <span className="text-primary">{candidates.length}개</span>
      </h2>
      <div className="mt-4 rounded-card bg-surface px-4 shadow-sm ring-1 ring-line sm:px-6">
        {candidates.map(candidate => (
          <AdditionalCoverageRow key={candidate.id} candidate={candidate} />
        ))}
      </div>
    </section>
  );
}

export function AdditionalCoverageResult({
  data,
  onRestart,
}: {
  data: AdditionalCoverageResultData;
  onRestart: () => void;
}) {
  return (
    <>
      <CoverageGrowthChart data={data} />
      <AdditionalCoverageNotice explanation={data.explanation} />
      <AdditionalCoverageList candidates={data.candidates} />

      <div className="mt-8 grid gap-3 sm:mx-auto sm:max-w-2xl sm:grid-cols-2">
        <Button type="button" variant="outline" size="lg" onClick={onRestart}>
          처음으로 돌아가기
        </Button>
        <Button type="button" size="lg">
          <Download />
          추가 보장 확인하기
        </Button>
      </div>

      <div className="mt-3 flex justify-center">
        <Button type="button" variant="ghost" size="sm" onClick={onRestart}>
          <RotateCcw />
          새로운 상황 분석하기
        </Button>
      </div>
    </>
  );
}
