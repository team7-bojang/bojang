import { AnimatePresence } from 'framer-motion';
import { Info, Search } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { INSURER_LIST } from '../data/insurers';
import type { PolicyOption } from '../model';
import { PolicyCard } from './PolicyCard';

interface PolicySelectorProps {
  policies: PolicyOption[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  loading?: boolean;
  className?: string;
  /** 선택 갯수 제한 — 'single'은 한 개만, 'multiple'은 여러 개. 기본값 'multiple'. */
  selectionMode?: 'single' | 'multiple';
  /** 현재 진행 중인 분석 플로우 이름 (예: "청구가능 보험 확인하기"). 배지로 표시. */
  flowLabel?: string;
}

const ALL = 'all';

/** "가입된 보험 선택" — 보험사 필터 + 검색 + 보험 카드 그리드. */
export function PolicySelector({
  policies,
  selectedIds,
  onToggle,
  loading = false,
  className,
  selectionMode = 'multiple',
  flowLabel,
}: PolicySelectorProps) {
  const [insurerFilter, setInsurerFilter] = useState(ALL);
  const [keyword, setKeyword] = useState('');

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    return policies.filter(policy => {
      const matchesInsurer = insurerFilter === ALL || policy.insurerId === insurerFilter;
      const matchesKeyword = q.length === 0 || policy.name.toLowerCase().includes(q);
      return matchesInsurer && matchesKeyword;
    });
  }, [policies, insurerFilter, keyword]);

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6',
        className
      )}
    >
      <div className="shrink-0">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <h2 className="text-lg font-bold text-ink">가입된 보험을 선택해주세요</h2>
          {flowLabel && (
            <span className="rounded-full bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
              {flowLabel}
            </span>
          )}
        </div>
        <p className="mt-1 flex items-center gap-1 text-sm font-medium text-primary">
          <Info className="size-3.5 shrink-0" />
          {selectionMode === 'single'
            ? '보험을 한 개만 선택할 수 있어요'
            : '보험을 여러 개 선택할 수 있어요'}
        </p>
      </div>

      <div className="mt-5 flex shrink-0 flex-col gap-3 sm:flex-row">
        <Select value={insurerFilter} onValueChange={setInsurerFilter}>
          <SelectTrigger className="sm:w-36">
            <SelectValue placeholder="전체" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>전체</SelectItem>
            {INSURER_LIST.map(insurer => (
              <SelectItem key={insurer.id} value={insurer.id}>
                {insurer.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="relative flex-1">
          <Input
            value={keyword}
            onChange={event => setKeyword(event.target.value)}
            placeholder="보험명을 입력해주세요"
            className="pr-10"
          />
          <Search className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
        </div>
      </div>

      <div className="scrollbar-primary mt-5 grid content-start items-start gap-3 py-1 sm:grid-cols-2 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:pr-2">
        {loading ? (
          <PolicySelectorSkeleton />
        ) : filtered.length === 0 ? (
          <p className="col-span-full py-10 text-center text-sm text-muted">
            조건에 맞는 보험이 없습니다.
          </p>
        ) : (
          <AnimatePresence mode="popLayout">
            {filtered.map((policy, index) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                index={index}
                selected={selectedIds.has(policy.id)}
                onToggle={onToggle}
              />
            ))}
          </AnimatePresence>
        )}
      </div>
    </section>
  );
}

function PolicySelectorSkeleton() {
  return (
    <>
      {[0, 1, 2, 3].map(item => (
        <div
          key={item}
          className="rounded-card border border-line bg-surface p-4 shadow-sm"
          aria-hidden="true"
        >
          <div className="flex items-start gap-3">
            <div className="size-10 shrink-0 animate-pulse rounded-xl bg-line/70" />
            <div className="min-w-0 flex-1 space-y-2 pt-1">
              <div className="h-4 w-20 animate-pulse rounded-full bg-line/70" />
              <div className="h-4 w-full max-w-44 animate-pulse rounded-full bg-line/70" />
            </div>
          </div>
          <div className="mt-4 flex gap-1.5">
            <div className="h-6 w-16 animate-pulse rounded-full bg-line/70" />
            <div className="h-6 w-14 animate-pulse rounded-full bg-line/70" />
          </div>
        </div>
      ))}
    </>
  );
}
