import type { CaseDashboard } from '@/types/case';
import { Field, NumberField } from './controls';

interface VisitSectionProps {
  form: CaseDashboard;
  patch: (partial: Partial<CaseDashboard>) => void;
}

/** 결제 금액, 진단 날짜, 연간 진료 횟수 입력 영역. */
export function VisitSection({ form, patch }: VisitSectionProps) {
  return (
    <div className="mt-6 grid gap-6 sm:grid-cols-2">
      <Field label="결제 금액" required>
        <NumberField
          value={form.payment_amount}
          onChange={v => patch({ payment_amount: v })}
          placeholder="예) 250000"
          suffix="원"
        />
      </Field>

      <Field label="연간 진료 횟수" required>
        <NumberField
          value={form.annual_visit_count}
          onChange={v => patch({ annual_visit_count: v })}
          placeholder="예) 3"
          suffix="회"
        />
      </Field>
    </div>
  );
}
