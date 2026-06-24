import { Search } from 'lucide-react';

import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { CaseDashboard } from '@/types/case';
import { Field, NumberField } from './controls';

interface DiagnosisSectionProps {
  form: CaseDashboard;
  patch: (partial: Partial<CaseDashboard>) => void;
}

/** 질병명 · 입/통원 · (입원 시) 입원 상세. */
export function DiagnosisSection({ form, patch }: DiagnosisSectionProps) {
  const inOut = form.is_inpatient ? 'inpatient' : form.is_outpatient ? 'outpatient' : '';

  return (
    <>
      <div className="grid gap-6 sm:grid-cols-2">
        <Field label="질병명 (KCD)" required>
          <div className="relative">
            <Input
              value={form.disease_name}
              placeholder="질병명 또는 KCD 코드를 입력하세요"
              onChange={event => patch({ disease_name: event.target.value })}
              className="pr-10"
            />
            <Search className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
          </div>
          {form.disease_kcd && (
            <span className="text-xs text-muted">KCD 코드: {form.disease_kcd}</span>
          )}
        </Field>

        <Field label="입/통원 여부" required>
          <RadioGroup
            className="flex gap-6 pt-2"
            value={inOut}
            onValueChange={value =>
              patch({
                is_inpatient: value === 'inpatient',
                is_outpatient: value === 'outpatient',
              })
            }
          >
            <label className="flex items-center gap-2 text-sm text-ink">
              <RadioGroupItem value="inpatient" /> 입원
            </label>
            <label className="flex items-center gap-2 text-sm text-ink">
              <RadioGroupItem value="outpatient" /> 통원
            </label>
          </RadioGroup>
        </Field>
      </div>

      {/* 입원 상세 — 입원일 때만 노출 */}
      {form.is_inpatient && (
        <div className="mt-5 grid gap-5 rounded-card border-2 border-dashed border-line p-5 sm:grid-cols-3">
          <Field label="수술 여부" required>
            <RadioGroup
              className="flex gap-6 pt-2"
              value={form.surgery ? 'yes' : 'no'}
              onValueChange={value => patch({ surgery: value === 'yes' })}
            >
              <label className="flex items-center gap-2 text-sm text-ink">
                <RadioGroupItem value="yes" /> 수술함
              </label>
              <label className="flex items-center gap-2 text-sm text-ink">
                <RadioGroupItem value="no" /> 수술하지 않음
              </label>
            </RadioGroup>
          </Field>

          <Field label="현재 입원일수">
            <NumberField
              value={form.admission_days_current}
              onChange={v => patch({ admission_days_current: v })}
              placeholder="예) 5"
              suffix="일"
            />
          </Field>

          <Field label="진단 입원일수">
            <NumberField
              value={form.admission_days_diagnosed}
              onChange={v => patch({ admission_days_diagnosed: v })}
              placeholder="예) 7"
              suffix="일"
            />
          </Field>
        </div>
      )}
    </>
  );
}
