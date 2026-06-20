import { Check } from 'lucide-react';

import { cn } from '@/lib/utils';

const STEPS = ['보험 선택·상황', '입력 확인', '분석 결과'] as const;

interface StepperProps {
  /** 현재 단계 (1-based). */
  current: number;
}

/** 3단계 진행 표시기. */
export function Stepper({ current }: StepperProps) {
  return (
    <ol className="flex items-center gap-2 sm:gap-3">
      {STEPS.map((label, index) => {
        const step = index + 1;
        const done = step < current;
        const active = step === current;

        return (
          <li key={label} className="flex items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  'relative flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-colors',
                  (done || active) && 'animate-step-node bg-primary text-white',
                  !done && !active && 'bg-canvas text-muted'
                )}
              >
                {active && (
                  <span
                    className="animate-step-ping pointer-events-none absolute inset-0 -z-10 rounded-full bg-primary/25"
                    aria-hidden="true"
                  />
                )}
                {done ? <Check className="size-4" strokeWidth={3} /> : step}
              </span>
              <span
                className={cn(
                  'text-sm font-semibold transition-colors',
                  active ? 'text-ink' : 'text-muted'
                )}
              >
                {label}
              </span>
            </div>
            {step < STEPS.length && (
              <span className="relative h-px w-6 overflow-hidden bg-line sm:w-10">
                <span
                  className={cn(
                    'absolute inset-y-0 left-0 bg-primary',
                    step < current ? 'animate-step-line' : 'w-0'
                  )}
                />
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
