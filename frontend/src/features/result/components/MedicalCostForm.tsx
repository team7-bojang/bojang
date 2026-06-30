import { useState } from 'react';

import { Button } from '@/components/ui/button';

import type { MedicalCostInput } from '../model';

interface MedicalCostFormProps {
  /** 이미 입력된 값(복원용). */
  initial: MedicalCostInput;
  submitting: boolean;
  /** 급여 본인부담금 / 비급여 의료비를 한 번에 전달한다. */
  onApply: (costs: MedicalCostInput) => void;
}

const onlyDigits = (value: string) => value.replace(/[^0-9]/g, '');
const formatComma = (digits: string) => (digits ? Number(digits).toLocaleString('ko-KR') : '');
const toInputValue = (value: number | undefined) => (value !== undefined ? String(value) : '');

export function MedicalCostForm({ initial, submitting, onApply }: MedicalCostFormProps) {
  const [patientPaid, setPatientPaid] = useState(() => toInputValue(initial.patient_paid_amount));

  const [nonCovered, setNonCovered] = useState(() => toInputValue(initial.non_covered_amount));

  const handleApply = () => {
    onApply({
      patient_paid_amount: patientPaid ? Number(patientPaid) : undefined,
      non_covered_amount: nonCovered ? Number(nonCovered) : undefined,
    });
  };

  const hasInput = Number(patientPaid) > 0 || Number(nonCovered) > 0;

  return (
    <div className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
      <h3 className="text-md font-bold text-ink">실손 병원비 입력</h3>

      <p className="mt-1 text-sm font-medium text-muted">
        병원비를 급여 본인부담금과 비급여로 나눠 입력하면 실손 예상 보험금을 계산해드려요.
      </p>

      <div className="mt-4 space-y-2">
        <label className="flex items-center gap-3 rounded-xl border border-line bg-canvas/60 px-3 py-2 sm:px-4">
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-bold text-ink">급여 본인부담금</span>
            <span className="block text-xs font-medium text-muted">
              영수증의 본인부담금(일부본인부담) 금액
            </span>
          </span>

          <span className="flex shrink-0 items-center gap-1">
            <input
              inputMode="numeric"
              value={formatComma(patientPaid)}
              onChange={e => setPatientPaid(onlyDigits(e.target.value))}
              placeholder="0"
              className="w-24 rounded-xl border border-line bg-surface px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
            />
            <span className="text-sm font-medium text-muted">원</span>
          </span>
        </label>

        <label className="flex items-center gap-3 rounded-xl border border-line bg-canvas/60 px-3 py-2 sm:px-4">
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-bold text-ink">비급여 의료비</span>
            <span className="block text-xs font-medium text-muted">
              영수증의 비급여 금액 (3대 비급여 포함)
            </span>
          </span>

          <span className="flex shrink-0 items-center gap-1">
            <input
              inputMode="numeric"
              value={formatComma(nonCovered)}
              onChange={e => setNonCovered(onlyDigits(e.target.value))}
              placeholder="0"
              className="w-24 rounded-xl border border-line bg-surface px-3 py-2 text-right text-sm font-semibold text-ink outline-none focus:border-primary sm:w-36"
            />
            <span className="text-sm font-medium text-muted">원</span>
          </span>
        </label>
      </div>

      <Button
        type="button"
        size="lg"
        className="mt-4 w-full"
        disabled={submitting || !hasInput}
        onClick={handleApply}
      >
        {submitting ? '계산 중...' : '실손 보험금 계산하기'}
      </Button>
    </div>
  );
}
