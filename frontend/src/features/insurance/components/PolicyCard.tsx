import { motion } from 'framer-motion';

import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { INSURERS } from '../data/insurers';
import type { Policy } from '../data/policies';

interface PolicyCardProps {
  policy: Policy;
  selected: boolean;
  onToggle: (id: string) => void;
  /** 등장 스태거 지연 계산용 (선택). */
  index?: number;
}

/** 단일 보험 상품 카드 (다중 선택). */
export function PolicyCard({ policy, selected, onToggle, index = 0 }: PolicyCardProps) {
  const insurer = INSURERS[policy.insurerId];

  return (
    <motion.label
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22, delay: Math.min(index, 8) * 0.035 }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.99 }}
      className={cn(
        'flex cursor-pointer flex-col gap-3 rounded-card border bg-surface p-4 shadow-sm transition-colors hover:shadow-md',
        selected ? 'border-primary ring-1 ring-primary/30' : 'border-line hover:border-primary/40'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-line bg-surface p-1.5">
            <img
              src={insurer.logo}
              alt={`${insurer.name} 로고`}
              className="h-full w-full object-contain"
            />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-ink">{insurer.name}</p>
            <p className="truncate text-sm text-muted">{policy.name}</p>
          </div>
        </div>
        <Checkbox
          checked={selected}
          onCheckedChange={() => onToggle(policy.id)}
          aria-label={`${policy.name} 선택`}
        />
      </div>

      <div className="flex flex-wrap gap-1.5 ">
        {policy.tags.map(tag => (
          <span
            key={tag}
            className="rounded-full border items-center border-line px-2.5 py-0.5 text-xs font-medium text-muted"
          >
            {tag}
          </span>
        ))}
      </div>
    </motion.label>
  );
}
