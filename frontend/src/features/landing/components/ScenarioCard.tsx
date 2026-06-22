import { MessageCircleQuestion } from 'lucide-react';

import type { Scenario } from '@/features/landing/data/scenarios';

/** 마퀴에 표시할 질문형 시나리오 단일 카드. */
export function ScenarioCard({ scenario }: { scenario: Scenario }) {
  return (
    <div className="mr-5 flex w-80 shrink-0 flex-col gap-3 rounded-card bg-surface p-5 shadow-sm ring-1 ring-line">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-full bg-primary-tint text-primary">
          <MessageCircleQuestion className="size-4" />
        </span>
        <span className="rounded-full bg-canvas px-2 py-0.5 text-xs font-medium text-muted">
          {scenario.tag}
        </span>
      </div>
      <p className="text-sm font-semibold leading-6 text-ink">{scenario.question}</p>
    </div>
  );
}
