import { CalendarDays, X } from 'lucide-react';

import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import type { CaseDashboard } from '@/types/case';
import { Field, NumberField } from './controls';
import { toISODate } from '../utils/date';

interface VisitSectionProps {
  form: CaseDashboard;
  patch: (partial: Partial<CaseDashboard>) => void;
  onAddVisitDate: (date: string) => void;
  onRemoveVisitDate: (date: string) => void;
}

/** 결제 금액, 진단 날짜, 연간 진료 횟수 입력 영역. */
export function VisitSection({
  form,
  patch,
  onAddVisitDate,
  onRemoveVisitDate,
}: VisitSectionProps) {
  return (
    <div className="mt-6 grid gap-6 sm:grid-cols-3">
      <Field label="결제 금액" required>
        <NumberField
          value={form.payment_amount}
          onChange={v => patch({ payment_amount: v })}
          placeholder="예) 250000"
          suffix="원"
        />
      </Field>

      <Field label="병원 진단 날짜" required>
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              className="flex h-11 w-full items-center gap-2 rounded-xl border border-line bg-surface px-4 text-left text-sm text-muted transition-colors hover:border-primary/40"
            >
              <CalendarDays className="size-4 shrink-0" />
              날짜 선택
            </button>
          </PopoverTrigger>
          <PopoverContent>
            <Calendar mode="single" onSelect={date => date && onAddVisitDate(toISODate(date))} />
          </PopoverContent>
        </Popover>
        {form.visit_dates.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {form.visit_dates.map(date => (
              <span
                key={date}
                className="inline-flex items-center gap-1 rounded-full bg-primary-tint px-2.5 py-0.5 text-xs font-medium text-primary"
              >
                {date}
                <button
                  type="button"
                  onClick={() => onRemoveVisitDate(date)}
                  aria-label="날짜 삭제"
                >
                  <X className="size-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </Field>

      <Field label="연간 진료 횟수" required>
        <NumberField
          value={form.annual_visit_count}
          onChange={v => patch({ annual_visit_count: v ?? 0 })}
          placeholder="예) 3"
          suffix="회"
        />
      </Field>
    </div>
  );
}
