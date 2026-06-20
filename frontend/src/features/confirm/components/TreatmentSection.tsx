import { Info } from 'lucide-react';

import type { CaseDashboard } from '@/types/case';
import { Chip, Field } from './controls';

const TREATMENT_OPTIONS = [
  'MRI',
  '도수치료',
  '물리치료',
  '주사치료',
  '체외충격파',
  '내시경',
  '초음파',
];

interface TreatmentSectionProps {
  form: CaseDashboard;
  onToggleTreatment: (item: string) => void;
}

/** 추가 치료 항목 선택 영역. */
export function TreatmentSection({ form, onToggleTreatment }: TreatmentSectionProps) {
  const treatmentOptions = Array.from(new Set([...TREATMENT_OPTIONS, ...form.treatment_items]));

  return (
    <div className="mt-6">
      <Field label="추가 치료 (복수 선택)" hint={<Info className="size-3.5 text-muted" />}>
        <div className="flex flex-wrap gap-2">
          {treatmentOptions.map(item => (
            <Chip
              key={item}
              active={form.treatment_items.includes(item)}
              onClick={() => onToggleTreatment(item)}
            >
              {item}
            </Chip>
          ))}
        </div>
      </Field>
    </div>
  );
}
