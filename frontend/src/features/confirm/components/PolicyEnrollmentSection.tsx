import type { CaseDashboard } from '@/types/case';
import { POLICY_ELAPSED_OPTIONS } from '@/features/confirm/policyElapsed';
import { Chip, Field } from './controls';

interface PolicyEnrollmentSectionProps {
  form: CaseDashboard;
  patch: (partial: Partial<CaseDashboard>) => void;
}

/** 가입 경과일 선택 입력 영역. */
export function PolicyEnrollmentSection({ form, patch }: PolicyEnrollmentSectionProps) {
  return (
    <div className="mt-6 border-t border-line pt-5">
      <Field label="가입 경과일">
        <div className="flex flex-wrap gap-2">
          {POLICY_ELAPSED_OPTIONS.map(option => {
            const selected = form.policy_elapsed_days === option.days;

            return (
              <Chip
                key={option.value}
                onClick={() => patch({ policy_elapsed_days: option.days })}
                active={selected}
              >
                {option.label}
              </Chip>
            );
          })}
        </div>
      </Field>
    </div>
  );
}
