import { useEffect, useState } from 'react';
import { AlertTriangle, ShieldCheck, Sparkles } from 'lucide-react';

import type { ServiceType } from '@/types/case';

import { LoadingMiniGame } from './LoadingMiniGame';

interface AnalysisLoadingScreenProps {
  serviceType: ServiceType;
}

const serviceCopy: Record<ServiceType, { title: string; description: string; steps: string[] }> = {
  CASE1: {
    title: '청구 가능한 보장을 분석하고 있습니다',
    description: '입력하신 진단·치료 정보와 선택한 보험 약관을 대조하고 있습니다.',
    steps: ['보장 조건 확인', '기청구 보험 제외', '청구 가능성 판정'],
  },
  CASE2: {
    title: '추가로 받을 수 있는 입원 보장을 비교하고 있습니다',
    description: '현재 입원일수와 진단 기준 입원일수를 비교해 추가 보장 가능성을 계산합니다.',
    steps: ['입원일수 비교', '일당·한도 조건 확인', '추가 지급 가능성 판정'],
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
      <div className="bg-ink-deep px-4 pt-4 sm:px-6 sm:pt-6">
        <LoadingMiniGame />
        <div className="mt-4 pb-5">
          <div className="flex items-center justify-between gap-3 text-sm font-semibold text-white">
            <span>분석 진행률</span>
            <span>{progress}%</span>
          </div>
          <div className="mt-2 h-4 overflow-hidden rounded-full border border-white/25 bg-black/35 p-0.5">
            <div
              className="h-full rounded-full bg-linear-to-r from-primary-soft via-chart-gain to-success-tint transition-[width] duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <span className="flex size-12 items-center justify-center rounded-full bg-primary-tint text-primary">
            <Sparkles className="size-6" />
          </span>
          <div>
            <p className="text-sm font-semibold text-primary">분석 진행 중</p>
            <h2 className="mt-1 text-xl font-bold text-ink sm:text-2xl">{copy.title}</h2>
          </div>
        </div>

        <p className="mt-5 max-w-2xl text-sm leading-6 text-muted">{copy.description}</p>

        <div className="mt-7 grid gap-3 sm:grid-cols-3">
          {copy.steps.map((step, index) => (
            <div key={step} className="rounded-card border border-line bg-canvas p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-muted">0{index + 1}</span>
                <ShieldCheck className="size-4 text-primary" />
              </div>
              <p className="mt-3 text-sm font-semibold text-ink">{step}</p>
            </div>
          ))}
        </div>

        <div className="mt-7 rounded-card border border-amber-200 bg-amber-50 p-4 text-amber-900">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" />
            <div>
              <p className="text-sm font-bold">현재 페이지를 벗어나면 분석이 취소됩니다.</p>
              <p className="mt-1 text-sm leading-6">
                결과 페이지로 이동할 때까지 새로고침하거나 뒤로 가기, 탭 닫기를 하지 말고 잠시만
                기다려주세요.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
