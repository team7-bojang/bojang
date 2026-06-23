import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { HeroFlowAnimation } from '@/features/landing/components/HeroFlowAnimation';
import { RotatingHeadline } from '@/features/landing/components/RotatingHeadline';

/** 1페이지: 히어로 (카피 + CTA + 흐름 애니메이션). */
export function HeroSection() {
  return (
    <section className="flex min-h-screen items-center bg-linear-to-b from-surface to-primary-tint/40">
      <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(360px,440px)] lg:py-24">
        <div className="flex flex-col gap-6">
          <span className="inline-flex w-fit items-center rounded-full bg-primary-tint px-3 py-1 text-base font-semibold text-primary">
            AI가 찾아주는 내 보험의 숨은 혜택
          </span>

          <h1 className="text-5xl font-extrabold leading-tight text-ink sm:text-6xl">
            이미 낸 보험료
            <RotatingHeadline className="mt-1" />
          </h1>

          <p className="text-lg text-muted">어떤 도움이 필요하신가요?</p>

          <div className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/home">
                청구가능보험 확인하기
                <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/home">
                추가보장찾기 시작하기
                <ArrowRight />
              </Link>
            </Button>
          </div>

          {/* 신뢰 지표 — 제품 사실 기반 (누적 통계 등 미보유 데이터는 사용하지 않음) */}
          <dl className="mt-6 flex flex-wrap gap-x-10 gap-y-4 border-t border-line pt-6">
            {[
              ['2가지', '분석 모드'],
              ['AI', '자동 분석'],
              ['100%', '약관 원문 근거'],
            ].map(([value, label]) => (
              <div key={label}>
                <dt className="text-2xl font-extrabold tabular-nums text-primary">{value}</dt>
                <dd className="mt-1 text-sm text-muted">{label}</dd>
              </div>
            ))}
          </dl>
        </div>

        <HeroFlowAnimation className="w-full" />
      </div>
    </section>
  );
}
