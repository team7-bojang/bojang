import type { ServiceType } from '@/types/case';

import { AmountTiles } from './AmountTiles';
import { FallingSadEmojis } from './FallingSadEmojis';
import { FireworkBurst } from './FireworkBurst';

interface ResultHeroProps {
  amount: number;
  hasPayableBenefits: boolean;
  serviceType: ServiceType;
}

export function ResultHero({ amount, hasPayableBenefits, serviceType }: ResultHeroProps) {
  const isCompare = serviceType === 'CASE2';

  return (
    <section className="animate-result-enter relative overflow-hidden py-8 text-center">
      {hasPayableBenefits && (
        <>
          <FireworkBurst className="left-2 top-0 sm:left-8 sm:top-2" />
          <FireworkBurst className="right-0 top-8 sm:right-8 sm:top-10" delay={0.72} />
          <FireworkBurst className="left-20 top-24 hidden sm:block" delay={1.48} />
          <FireworkBurst className="right-24 top-28 hidden sm:block" delay={2.22} />
        </>
      )}
      {!hasPayableBenefits && <FallingSadEmojis />}

      <div className="relative z-10">
        <div className="font-tossface mx-auto flex size-12 items-center justify-center rounded-full bg-primary-tint text-2xl shadow-sm sm:size-14 sm:text-3xl">
          {hasPayableBenefits ? '🎉' : '🥲'}
        </div>
        <h1 className="mt-5 text-4xl font-black tracking-normal text-ink">분석이 완료됐어요</h1>
        <p className="mt-3 text-lg font-medium text-muted">
          {isCompare
            ? '입원 기간에 따라 달라지는 추가 보장을 비교했어요.'
            : hasPayableBenefits
              ? '현재 조건에서 청구 가능한 보장을 찾았어요.'
              : '현재 조건에서 바로 청구 가능한 보장은 확인되지 않았어요.'}
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
