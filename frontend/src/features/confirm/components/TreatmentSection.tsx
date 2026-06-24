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
}: TreatmentSectionProps) {
  const selectedItems = form.treatment_items;
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
      : (firstSelectedGroup ?? groups[0] ?? null);
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
            {groups.map(group => (
              <Chip
                key={group}
                onClick={() => setActiveGroup(group)}
                active={currentGroup === group}
                variant="group"
              >
                {group}
              </Chip>
            ))}
          </div>

          {currentGroup && (
            <div className="mt-4 border-t border-line pt-4">
              <div className="flex flex-wrap gap-2">
                {activeGroupOptions.map(type => {
                  const selected =
                    selectedItems.includes(type.code) || selectedItems.includes(type.displayName);

                  return (
                    <Chip
                      key={type.code}
                      onClick={() => onToggleTreatment(type.displayName, type.code)}
                      active={selected}
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
