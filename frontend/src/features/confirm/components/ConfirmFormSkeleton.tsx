import { cn } from '@/lib/utils';

function Skeleton({ className }: { className: string }) {
  return <div className={cn('animate-pulse rounded-lg bg-line/70', className)} />;
}

/** 상황 입력 데이터를 불러오는 동안 실제 폼 구조를 미리 보여주는 스켈레톤. */
export function ConfirmFormSkeleton() {
  return (
    <div
      className="mt-6 rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-7"
      aria-busy="true"
      aria-label="입력 내용 불러오는 중"
    >
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

      <div className="mt-5 grid gap-5 rounded-card border-2 border-dashed border-line p-5 sm:grid-cols-3">
        {[0, 1, 2].map(item => (
          <div key={item} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        ))}
      </div>

      <div className="mt-6 space-y-3">
        <Skeleton className="h-4 w-36" />
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2, 3, 4, 5, 6].map(item => (
            <Skeleton key={item} className="h-8 w-20 rounded-full" />
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-3">
        {[0, 1, 2].map(item => (
          <div key={item} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        ))}
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(14rem,18rem)] sm:items-center">
            <Skeleton className="h-5 w-full max-w-sm" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        {[0, 1].map(item => (
          <div key={item} className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <div className="flex min-h-11 flex-wrap items-center gap-2 rounded-xl border border-line bg-canvas px-3 py-2">
              <Skeleton className="h-6 w-24 rounded-full" />
              <Skeleton className="h-6 w-28 rounded-full" />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-col items-stretch justify-between gap-3 rounded-card bg-canvas p-4 sm:flex-row sm:items-center">
        <Skeleton className="h-5 w-full max-w-md" />
        <Skeleton className="h-11 w-full rounded-xl sm:w-44" />
      </div>
    </div>
  );
}
