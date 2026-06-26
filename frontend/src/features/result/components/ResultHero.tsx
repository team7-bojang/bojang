import type { ServiceType } from '@/types/case';

import { AmountTiles } from './AmountTiles';
import { FallingSadEmojis } from './FallingSadEmojis';
import { ResultConfetti } from './ResultConfetti';

interface ResultHeroProps {
  amount: number | null;
  payableCount: number;
  hasPayableBenefits: boolean;
  serviceType: ServiceType;
}

export function ResultHero({
  amount,
  payableCount,
  hasPayableBenefits,
  serviceType,
}: ResultHeroProps) {
  const isCompare = serviceType === 'CASE2';
  const summaryText = isCompare
    ? '입원 기간에 따른 추가 보장을 비교했습니다'
    : hasPayableBenefits
      ? `청구 가능한 보장을 ${payableCount}개 찾았습니다`
      : '현재 조건에서 바로 청구 가능한 보장은 확인되지 않았습니다';

  return (
    <section className="animate-result-enter relative overflow-hidden py-6 text-center sm:py-8">
      {!hasPayableBenefits && <FallingSadEmojis />}

      <div className="relative z-10">
        <div className="font-tossface mx-auto flex size-11 items-center justify-center rounded-full bg-primary-tint text-2xl shadow-sm sm:size-12">
          {hasPayableBenefits ? '🎉' : '😢'}
        </div>
        <h1 className="relative mx-auto mt-4 inline-block text-3xl font-extrabold tracking-normal text-ink sm:text-4xl">
          {hasPayableBenefits && (
            <>
              <ResultConfetti side="left" />
              <ResultConfetti side="right" />
            </>
          )}
          분석이 완료되었습니다!
        </h1>
        <p className="mt-2 text-base font-bold text-muted sm:text-lg">{summaryText}</p>

        <div className="mt-7">
          <p className="mb-3 text-base font-bold text-ink">
            {isCompare ? '추가 예상 보험금' : '약관기준 산정금액'}
          </p>
          <AmountTiles amount={amount} />
        </div>
      </div>
    </section>
  );
}
