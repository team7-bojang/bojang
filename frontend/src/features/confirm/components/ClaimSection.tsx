import { Chip, Field } from './controls';

export interface ClaimOption {
  id: string;
  label: string;
}

interface ClaimSectionProps {
  claimOptions: ClaimOption[];
  claimedPolicyIds: string[];
  analysisTargets: ClaimOption[];
  onToggleClaimed: (id: string) => void;
}

/** 기청구 보험과 분석 대상 보험 선택 영역. */
export function ClaimSection({
  claimOptions,
  claimedPolicyIds,
  analysisTargets,
  onToggleClaimed,
}: ClaimSectionProps) {
  return (
    <div className="mt-6 grid gap-6 sm:grid-cols-2">
      <Field label="이미 청구한 보험(복수 선택)">
        {claimOptions.length === 0 ? (
          <p className="text-sm text-muted">이전 화면에서 선택하거나 업로드한 보험이 없습니다.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {claimOptions.map(option => (
              <Chip
                key={option.id}
                active={claimedPolicyIds.includes(option.id)}
                onClick={() => onToggleClaimed(option.id)}
              >
                {option.label}
              </Chip>
            ))}
          </div>
        )}
      </Field>

      <Field label="확인할 보험 " locked>
        <div className="flex min-h-11 flex-wrap content-center items-center gap-1.5 rounded-xl border border-line bg-canvas px-3 py-2">
          {analysisTargets.length === 0 ? (
            <span className="text-sm text-muted">자동으로 선택됩니다</span>
          ) : (
            analysisTargets.map(option => (
              <span
                key={option.id}
                className="inline-flex items-center justify-center rounded-full bg-surface px-2.5 py-1 text-xs font-medium leading-none text-ink ring-1 ring-line"
              >
                {option.label}
              </span>
            ))
          )}
        </div>
      </Field>
    </div>
  );
}
