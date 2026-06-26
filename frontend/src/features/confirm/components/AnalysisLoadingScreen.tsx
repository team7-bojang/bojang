import { useEffect, useState } from 'react';

import type { ServiceType } from '@/types/case';

import { LoadingMiniGame } from './LoadingMiniGame';

interface AnalysisLoadingScreenProps {
  serviceType: ServiceType;
}

const serviceCopy: Record<ServiceType, { title: string; description: string }> = {
  CASE1: {
    title: '청구 가능한 보장을 분석하고 있습니다',
    description: '입력하신 진단·치료 정보와 선택한 보험 약관을 대조하고 있습니다.',
  },
  CASE2: {
    title: '추가로 받을 수 있는 입원 보장을 비교하고 있습니다',
    description: '현재 입원일수와 진단 기준 입원일수를 비교해 추가 보장 가능성을 계산합니다.',
  },
};

/** 분석 요청이 끝나고 결과 페이지로 이동하기 전까지 보여주는 진행 화면. */
export function AnalysisLoadingScreen({ serviceType }: AnalysisLoadingScreenProps) {
  const copy = serviceCopy[serviceType];
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
      className="animate-confirm-form-enter mt-6 overflow-hidden rounded-card bg-surface shadow-sm ring-1 ring-line"
      aria-busy="true"
      aria-live="polite"
    >
      <div className="border-b border-line bg-canvas px-4 pt-4 sm:px-6 sm:pt-6">
        <LoadingMiniGame />
        <p className="mt-2 text-center text-xs text-muted">
          스페이스 · 클릭 · 터치로 점프하며 기다려보세요
        </p>
        <div className="mt-3 pb-5">
          <div className="flex items-center justify-between gap-3 text-sm font-semibold text-ink">
            <span>분석 진행률</span>
            <span>{progress}%</span>
          </div>
          <div className="mt-2 h-3 overflow-hidden rounded-full bg-line">
            <div
              className="h-full rounded-full bg-primary transition-[width] duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="p-6 text-center sm:p-8">
        <h2 className="text-lg font-bold text-ink sm:text-xl">{copy.title}</h2>
        <p className="mt-2 text-sm leading-6 text-muted">{copy.description}</p>
        <p className="mt-4 text-xs text-muted">
          새로고침·뒤로 가기·탭 닫기를 하면 분석이 취소돼요. 잠시만 기다려주세요.
        </p>
      </div>
    </section>
  );
}
