import { cn } from '@/lib/utils';

function Skeleton({ className }: { className: string }) {
  return <div className={cn('animate-pulse rounded-lg bg-line/70', className)} />;
}

/** 상황 입력 데이터를 불러오는 동안 실제 폼 구조를 미리 보여주는 스켈레톤. */
export function ConfirmFormSkeleton() {
  const sections = [
    { titleWidth: 'w-20', summaryWidth: 'w-72', open: true },
    { titleWidth: 'w-20', summaryWidth: 'w-44' },
    { titleWidth: 'w-32', summaryWidth: 'w-52' },
    { titleWidth: 'w-24', summaryWidth: 'w-32' },
    { titleWidth: 'w-20', summaryWidth: 'w-40' },
  ];

  return (
    <div
      className="mt-6 space-y-3 pb-40 sm:pb-32"
      aria-busy="true"
      aria-label="입력 내용 불러오는 중"
    >
      {sections.map((section, index) => (
        <section
          key={index}
          className="overflow-hidden rounded-card bg-surface shadow-sm ring-1 ring-line"
        >
          <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className={cn('h-4', section.titleWidth)} />
              <Skeleton className={cn('h-3 max-w-full', section.summaryWidth)} />
            </div>
            <Skeleton className="size-5 shrink-0 rounded-full" />
          </div>

          {section.open && (
            <div className="border-t border-line px-5 py-5 sm:px-6">
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-11 w-full rounded-xl" />
                  <Skeleton className="h-3 w-28" />
                </div>
                <div className="space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <div className="flex gap-4 pt-1">
                    <Skeleton className="h-6 w-20 rounded-full" />
                    <Skeleton className="h-6 w-20 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
