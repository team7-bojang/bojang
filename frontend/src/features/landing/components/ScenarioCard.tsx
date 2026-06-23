import { ArrowRight } from 'lucide-react';

import type { Scenario } from '@/features/landing/data/scenarios';

/** 마퀴에 표시할 질문형 시나리오 단일 카드. */
export function ScenarioCard({ scenario }: { scenario: Scenario }) {
  return (
    <div className="mr-5 flex w-88 shrink-0 flex-col gap-4 rounded-2xl bg-surface p-6 shadow-[0_10px_30px_-12px_rgba(13,110,102,0.25)]">
      <div className="flex items-center gap-2.5">
        <span className="font-tossface flex size-9 items-center justify-center rounded-full bg-primary-tint text-xl">
          {scenario.emoji}
        </span>
        <span className="rounded-full bg-primary-tint px-2.5 py-1 text-xs font-bold text-primary">
          {scenario.tag}
        </span>
      </div>

      <p className="text-base font-bold leading-7 text-ink">{scenario.question}</p>

      {/* 안쪽 강조 박스 — 카드에 입체감과 행동 유도를 더한다. */}
      <div className="mt-auto flex items-center justify-between rounded-xl bg-primary-tint/30 px-4 py-3">
        <span className="text-xs font-semibold text-muted">청구 가능성 분석</span>
        <span className="flex items-center gap-1 text-xs font-bold text-primary">
          확인하기
          <ArrowRight className="size-3.5" />
        </span>
      </div>
    </div>
  );
}
