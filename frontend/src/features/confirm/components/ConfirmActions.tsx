import { ArrowRight, Info } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ConfirmActionsProps {
  disabled: boolean;
  onSubmit: () => void;
  className?: string;
}

/** 확인 페이지 하단 안내와 제출 버튼. */
export function ConfirmActions({ disabled, onSubmit, className }: ConfirmActionsProps) {
  return (
    <div
      className={cn(
        'mt-6 flex flex-col items-stretch justify-between gap-3 rounded-card bg-canvas p-4 sm:flex-row sm:items-center',
        className
      )}
    >
      <p className="flex items-center gap-2 text-sm text-muted">
        <Info className="size-4 shrink-0 text-primary" />
        이미 청구한 보험을 제외하고 나머지 보험은 자동으로 확인해드려요
      </p>
      <Button type="button" size="lg" className="shrink-0" disabled={disabled} onClick={onSubmit}>
        입력 내용 확인 완료
        <ArrowRight />
      </Button>
    </div>
  );
}
