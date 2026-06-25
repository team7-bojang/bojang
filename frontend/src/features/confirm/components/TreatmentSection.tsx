import { Check, Info } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Tooltip } from '@/components/ui/tooltip';
import { getActiveTreatmentTypes } from '@/features/confirm/treatmentTypes';
import type { CaseDashboard, TreatmentType } from '@/types/case';
import { Chip, Field } from './controls';

interface NormalizedTreatmentType {
  code: string;
  uiGroup: string;
  displayName: string;
}

interface TreatmentSectionProps {
  form: CaseDashboard;
  treatmentTypes: TreatmentType[];
  onToggleTreatment: (displayName: string, code: string) => void;
  onSelectNone: () => void;
}

function normalizeTreatmentType(type: TreatmentType): NormalizedTreatmentType {
  return {
    code: type.code,
    uiGroup: type.ui_group || '기타',
    displayName: type.display_name || type.name || type.code,
  };
}

function groupTreatments(types: NormalizedTreatmentType[]) {
  return types.reduce<Record<string, NormalizedTreatmentType[]>>((groups, type) => {
    groups[type.uiGroup] = [...(groups[type.uiGroup] ?? []), type];
    return groups;
  }, {});
}

/** 추가 치료 항목 선택 영역. */
export function TreatmentSection({
  form,
  treatmentTypes,
  onToggleTreatment,
  onSelectNone,
}: TreatmentSectionProps) {
  const selectedItems = form.treatment_items;
  const hasNone = selectedItems.length === 0;
  const sourceTreatmentTypes = getActiveTreatmentTypes(treatmentTypes);
  const options = useMemo(() => {
    const activeTypes = sourceTreatmentTypes
      .filter(type => type.active !== false)
      .map(normalizeTreatmentType);
    const knownCodes = new Set(activeTypes.map(type => type.code));
    const knownDisplayNames = new Set(activeTypes.map(type => type.displayName));
    const unknownSelected = selectedItems
      .filter(item => !knownCodes.has(item) && !knownDisplayNames.has(item))
      .map(item => ({
        code: item,
        uiGroup: '기타',
        displayName: item,
      }));

    return [...activeTypes, ...unknownSelected];
  }, [selectedItems, sourceTreatmentTypes]);
  const groupedOptions = useMemo(() => groupTreatments(options), [options]);
  const groups = useMemo(() => Object.keys(groupedOptions), [groupedOptions]);
  const firstSelectedGroup = options.find(
    type => selectedItems.includes(type.code) || selectedItems.includes(type.displayName)
  )?.uiGroup;
  const [activeGroup, setActiveGroup] = useState<string | null>(null);
  const currentGroup =
    activeGroup && groupedOptions[activeGroup]
      ? activeGroup
      : (firstSelectedGroup ?? (hasNone ? null : (groups[0] ?? null)));
  const activeGroupOptions = currentGroup ? (groupedOptions[currentGroup] ?? []) : [];

  return (
    <div className="mt-6">
      <Field
        label="추가 진료 (복수 선택)"
        hint={
          <Tooltip label="검사·처치 항목을 선택하면 관련 특약 보장 가능성을 함께 확인합니다.">
            <Info className="size-3.5 text-muted" />
          </Tooltip>
        }
      >
        <div className="rounded-2xl border border-line bg-surface p-3">
          <div className="flex flex-wrap gap-2">
            <Chip
              active={hasNone && !currentGroup}
              onClick={() => {
                setActiveGroup(null);
                onSelectNone();
              }}
              className="border-dashed text-muted"
            >
              {hasNone && <Check className="size-3.5" />}
              <span>해당없음</span>
            </Chip>
            {groups.map(group => (
              <Chip
                key={group}
                onClick={() => setActiveGroup(group)}
                active={currentGroup === group}
                variant="group"
                className="px-4 py-2 text-sm font-semibold"
              >
                {group}
              </Chip>
            ))}
          </div>

          {currentGroup && (
            <div className="mt-4 rounded-xl border border-line bg-canvas/60 p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-xs font-bold text-muted">세부 치료 항목</span>
                <span className="rounded-full bg-surface px-2 py-1 text-xs font-semibold text-primary ring-1 ring-line">
                  {currentGroup}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {activeGroupOptions.map(type => {
                  const selected =
                    selectedItems.includes(type.code) || selectedItems.includes(type.displayName);

                  return (
                    <Chip
                      key={type.code}
                      onClick={() => onToggleTreatment(type.displayName, type.code)}
                      active={selected}
                      className="rounded-xl bg-white px-3.5 py-2 font-medium"
                    >
                      {selected && <Check className="size-3.5" />}
                      <span>{type.displayName}</span>
                    </Chip>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </Field>
    </div>
  );
}
