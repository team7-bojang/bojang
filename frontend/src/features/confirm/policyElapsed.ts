export const POLICY_ELAPSED_OPTIONS = [
  { label: '90일 미만', value: '90일 미만', days: 80 },
  { label: '90일 이상~1년 미만', value: '90일 이상~1년 미만', days: 180 },
  { label: '1년 이상~2년 미만', value: '1년 이상~2년 미만', days: 540 },
  { label: '2년 이상', value: '2년 이상', days: 730 },
  { label: '잘 모르겠어요', value: '잘 모르겠어요', days: null },
] as const;

export function getPolicyElapsedLabel(days: number | null) {
  return POLICY_ELAPSED_OPTIONS.find(option => option.days === days)?.label ?? '잘 모르겠어요';
}

export function getPolicyElapsedValue(days: number | null) {
  return POLICY_ELAPSED_OPTIONS.find(option => option.days === days)?.value ?? '잘 모르겠어요';
}
