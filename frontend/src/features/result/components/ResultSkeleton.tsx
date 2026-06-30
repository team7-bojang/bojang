import { cn } from '@/lib/utils';

function Skeleton({ className }: { className: string }) {
  return <div className={cn('animate-pulse rounded-lg bg-line/70', className)} />;
}

/** 분석 결과를 불러오는 동안 실제 결과(히어로 + 그래프 + 보장 목록) 구조를 미리 보여주는 스켈레톤. */
export function ResultSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="분석 결과 불러오는 중">
      {/* 히어로 — 제목·요약 */}
      <section className="rounded-card bg-surface p-6 shadow-sm ring-1 ring-line sm:p-8">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="mt-3 h-8 w-3/4 sm:h-10" />
        <Skeleton className="mt-3 h-4 w-1/2" />
      </section>

      {/* 그래프 카드 — 세로 막대 비교 자리 */}
      <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="mt-2 h-3 w-64 max-w-full" />
        <div className="mt-8 flex items-end justify-center gap-8 sm:gap-14">
          <div className="flex flex-col items-center gap-3">
            <Skeleton className="h-4 w-10" />
            <Skeleton className="h-28 w-24 rounded-t-xl sm:h-36 sm:w-28" />
          </div>
          <div className="flex flex-col items-center gap-3">
            <Skeleton className="h-4 w-10" />
            <Skeleton className="h-44 w-24 rounded-t-xl sm:h-56 sm:w-28" />
          </div>
        </div>
      </section>

      {/* 보장 목록 카드 */}
      <section className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
        <Skeleton className="h-5 w-48" />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="space-y-2 border-b border-line/70 pb-3 last:border-b-0">
              <Skeleton className="h-5 w-24 rounded-full" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
