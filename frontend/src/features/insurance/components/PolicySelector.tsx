import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { INSURER_LIST } from '../data/insurers';
import { PolicyCard } from './PolicyCard';
import type { PolicyOption } from '../model';

interface PolicySelectorProps {
  policies: PolicyOption[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  className?: string;
}

const ALL = 'all';

/** "선제시 보험 선택" — 보험사 필터 + 검색 + 보험 카드 그리드. */
export function PolicySelector({
  policies,
  selectedIds,
  onToggle,
  className,
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
      <h2 className="shrink-0 text-lg font-bold text-ink">선제시 보험 선택</h2>

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

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:pr-1  scrollbar-hide py-1">
        {filtered.length === 0 ? (
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
