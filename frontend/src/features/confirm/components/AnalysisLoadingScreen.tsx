import { useEffect, useState } from 'react';

import type { ServiceType } from '@/types/case';

import { AdvertisementRotator } from './AdvertisementRotator';

interface AnalysisLoadingScreenProps {
  serviceType: ServiceType;
}

const loadingSteps: Record<ServiceType, string[]> = {
  CASE1: ['가입 보장 확인 중', '약관 근거 대조 중', '결과 화면 준비 중'],
  CASE2: ['입원 일수 확인 중', '추가 보장 조건 대조 중', '결과 화면 준비 중'],
};

/** 분석 요청이 끝나고 결과 페이지로 이동하기 전까지 보여주는 진행 화면. */
export function AnalysisLoadingScreen({ serviceType }: AnalysisLoadingScreenProps) {
  const steps = loadingSteps[serviceType];
  const [progress, setProgress] = useState(7);

  useEffect(() => {
    let frameId = 0;
    let lastProgress = -1;
    const startedAt = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startedAt;
      const eased = 1 - Math.exp(-elapsed / 21000);
      const nextProgress = Math.min(94, 7 + eased * 89 + Math.sin(elapsed / 850) * 1.4);
      const rounded = Math.max(7, Math.round(nextProgress));

      if (rounded !== lastProgress) {
        lastProgress = rounded;
        setProgress(rounded);
      }

      frameId = window.requestAnimationFrame(tick);
    };

    frameId = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [serviceType]);

  return (
    <section
      className="animate-confirm-form-enter mt-6 overflow-hidden rounded-card bg-surface p-4 shadow-sm ring-1 ring-line sm:p-6"
      aria-busy="true"
      aria-live="polite"
    >
      <AdvertisementRotator />

      <div className="mt-5 rounded-2xl bg-canvas px-4 py-3 ring-1 ring-line">
        <div
          className="h-2 overflow-hidden rounded-full bg-line"
          role="progressbar"
          aria-label="분석 진행 상태"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <div
            className="h-full rounded-full bg-primary transition-[width] duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <ol className="mt-3 grid gap-2 text-xs font-semibold text-muted sm:grid-cols-3">
          {steps.map((step, index) => {
            const threshold = ((index + 1) / steps.length) * 94;
            const isReached = progress >= threshold;

            return (
              <li key={step} className="flex items-center gap-2">
                <span
                  className={[
                    'flex size-5 shrink-0 items-center justify-center rounded-full text-[0.68rem]',
                    isReached ? 'bg-primary text-white' : 'bg-surface text-muted ring-1 ring-line',
                  ].join(' ')}
                >
                  {index + 1}
                </span>
                <span className={isReached ? 'text-ink' : undefined}>{step}</span>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
