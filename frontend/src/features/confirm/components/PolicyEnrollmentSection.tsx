import { CalendarDays, X } from 'lucide-react';

import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Field } from './controls';

/** Date -> 'YYYY-MM-DD' (로컬 기준). */
function toISODate(date: Date): string {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10);
}

interface PolicyEnrollmentSectionProps {
  enrollmentDate: string | null;
  onChangeEnrollmentDate: (date: string | null) => void;
}

/** 가입일자 선택 입력 영역. */
export function PolicyEnrollmentSection({
  enrollmentDate,
  onChangeEnrollmentDate,
}: PolicyEnrollmentSectionProps) {
  return (
    <div className="mt-6 border-t border-line pt-5">
      <Field label="가입일자">
        <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(14rem,18rem)] sm:items-center">
          <p className="text-sm text-muted">
            선택사항입니다. 입력하면 상세한 분석에 더 도움이 됩니다.
          </p>
          <div className="flex gap-2">
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="flex h-11 min-w-0 flex-1 items-center gap-2 rounded-xl border border-line bg-surface px-4 text-left text-sm text-muted transition-colors hover:border-primary/40"
                >
                  <CalendarDays className="size-4 shrink-0" />
                  <span className="truncate">{enrollmentDate ?? '날짜 선택'}</span>
                </button>
              </PopoverTrigger>
              <PopoverContent>
                <Calendar
                  mode="single"
                  onSelect={date => date && onChangeEnrollmentDate(toISODate(date))}
                />
              </PopoverContent>
            </Popover>

            {enrollmentDate && (
              <button
                type="button"
                className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-line bg-surface text-muted transition-colors hover:border-primary/40 hover:text-ink"
                onClick={() => onChangeEnrollmentDate(null)}
                aria-label="가입일자 삭제"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        </div>
      </Field>
    </div>
  );
}
