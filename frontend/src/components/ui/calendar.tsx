import { ChevronLeft, ChevronRight } from 'lucide-react';
import { DayPicker } from 'react-day-picker';

import { cn } from '@/lib/utils';
import { buttonVariants } from './button';

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

/** shadcn 스타일 캘린더 (react-day-picker 기반). */
export function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn('p-3', className)}
      classNames={{
        months: 'flex flex-col gap-4',
        month: 'flex flex-col gap-4',
        month_caption: 'flex h-9 items-center justify-center',
        caption_label: 'text-sm font-semibold text-ink',
        nav: 'absolute inset-x-0 top-3 flex items-center justify-between px-3',
        button_previous: cn(buttonVariants({ variant: 'outline', size: 'icon' }), 'size-7 p-0'),
        button_next: cn(buttonVariants({ variant: 'outline', size: 'icon' }), 'size-7 p-0'),
        month_grid: 'w-full border-collapse',
        weekdays: 'flex',
        weekday: 'w-9 text-xs font-medium text-muted',
        week: 'mt-1 flex w-full',
        day: 'size-9 p-0 text-center text-sm',
        day_button: cn(
          buttonVariants({ variant: 'ghost', size: 'icon' }),
          'size-9 rounded-lg p-0 font-normal aria-selected:opacity-100'
        ),
        selected:
          '[&>button]:bg-primary [&>button]:text-white [&>button]:hover:bg-primary [&>button]:hover:text-white',
        today: '[&>button]:border [&>button]:border-primary [&>button]:text-primary',
        outside: 'text-muted/50',
        disabled: 'text-muted/40 opacity-50',
        hidden: 'invisible',
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation }) =>
          orientation === 'left' ? (
            <ChevronLeft className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          ),
      }}
      {...props}
    />
  );
}
