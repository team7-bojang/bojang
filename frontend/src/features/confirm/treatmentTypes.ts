import type { TreatmentType } from '@/types/case';

export const DEFAULT_TREATMENT_TYPES: TreatmentType[] = [
  {
    code: 'MRI_MRA',
    ui_group: '영상검사',
    display_name: 'MRI/MRA',
    active: true,
  },
  {
    code: 'CT',
    ui_group: '영상검사',
    display_name: 'CT 검사',
    active: true,
  },
  {
    code: 'XRAY',
    ui_group: '영상검사',
    display_name: '엑스레이',
    active: true,
  },
  {
    code: 'MANUAL_THERAPY',
    ui_group: '도수·충격파',
    display_name: '도수치료',
    active: true,
  },
  {
    code: 'ECSWT',
    ui_group: '도수·충격파',
    display_name: '체외충격파',
    active: true,
  },
  {
    code: 'INJECTION',
    ui_group: '주사치료',
    display_name: '주사치료',
    active: true,
  },
  {
    code: 'PHYSICAL_THERAPY',
    ui_group: '물리치료',
    display_name: '일반 물리치료',
    active: true,
  },
  {
    code: 'MEDICATION',
    ui_group: '기타',
    display_name: '약 처방',
    active: true,
  },
  {
    code: 'CAST',
    ui_group: '기타',
    display_name: '깁스',
    active: true,
  },
  {
    code: 'BRACE_SPLINT',
    ui_group: '기타',
    display_name: '보조기·부목',
    active: true,
  },
  {
    code: 'EMERGENCY',
    ui_group: '기타',
    display_name: '응급실 진료',
    active: true,
  },
  {
    code: 'OTHER',
    ui_group: '기타',
    display_name: '기타 치료',
    active: true,
  },
];

export function getActiveTreatmentTypes(treatmentTypes: TreatmentType[]) {
  return treatmentTypes.length > 0 ? treatmentTypes : DEFAULT_TREATMENT_TYPES;
}

export function getTreatmentDisplayName(value: string, treatmentTypes: TreatmentType[]) {
  const treatment = getActiveTreatmentTypes(treatmentTypes).find(
    type => type.code === value || type.display_name === value || type.name === value
  );

  return treatment?.display_name || treatment?.name || value;
}

export function getTreatmentCode(value: string, treatmentTypes: TreatmentType[]) {
  const treatment = getActiveTreatmentTypes(treatmentTypes).find(
    type => type.code === value || type.display_name === value || type.name === value
  );

  return treatment?.code ?? value;
}
