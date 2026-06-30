import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Check, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Chip as ConfirmChip } from '@/features/confirm/components/controls';
import { getActiveTreatmentTypes } from '@/features/confirm/treatmentTypes';
import type { TreatmentType } from '@/types/case';

import type { AnswerValue, NextQuestion, NormalizedOption } from '../model';
import { normalizeOptions } from '../options';
import { Chip } from './Chip';
import { DiseasePicker } from './DiseasePicker';

interface QuestionPromptProps {
  question: NextQuestion;
  onAnswer: (questionId: string, value: AnswerValue, label: string) => void;
  onTextInputRequest?: (request: { questionId: string; placeholder?: string }) => void;
  disabled?: boolean;
}

interface InnerProps {
  question: NextQuestion;
  onAnswer: QuestionPromptProps['onAnswer'];
  disabled: boolean;
}

export function QuestionPrompt({
  question,
  onAnswer,
  onTextInputRequest,
  disabled = false,
}: QuestionPromptProps) {
  if (question.input_type === 'select_button' && question.question_id === 'disease_kcd') {
    return (
      <DiseasePicker
        question={question}
        onAnswer={onAnswer}
        onTextInputRequest={onTextInputRequest}
        disabled={disabled}
      />
    );
  }
  if (question.input_type === 'checkbox_button') {
    if (question.question_id === 'treatment_items') {
      return <TreatmentItemPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
    }
    return <CheckboxPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
  }
  if (question.input_type === 'text_input') {
    return (
      <TextInputBridge
        question={question}
        onTextInputRequest={onTextInputRequest}
        fallback={<TextPrompt question={question} onAnswer={onAnswer} disabled={disabled} />}
      />
    );
  }
  if (question.input_type === 'file_upload') {
    return <FilePrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
  }
  return <RadioPrompt question={question} onAnswer={onAnswer} disabled={disabled} />;
}

function TextInputBridge({
  question,
  onTextInputRequest,
  fallback,
}: {
  question: NextQuestion;
  onTextInputRequest?: (request: { questionId: string; placeholder?: string }) => void;
  fallback: ReactNode;
}) {
  useEffect(() => {
    onTextInputRequest?.({
      questionId: question.question_id,
      placeholder: question.placeholder,
    });
  }, [onTextInputRequest, question.placeholder, question.question_id]);

  if (onTextInputRequest) {
    return null;
  }

  return fallback;
}

function RadioPrompt({ question, onAnswer, disabled }: InnerProps) {
  const options = normalizeOptions(question.options);

  return (
    <div className="flex flex-wrap gap-2">
      {options.map(opt => (
        <Chip
          key={String(opt.value)}
          label={opt.label}
          disabled={disabled}
          onClick={() => onAnswer(question.question_id, opt.value, opt.label)}
        />
      ))}
    </div>
  );
}

function CheckboxPrompt({ question, onAnswer, disabled }: InnerProps) {
  const options = normalizeOptions(question.options);
  const [selected, setSelected] = useState<NormalizedOption[]>([]);

  const toggle = (opt: NormalizedOption) => {
    setSelected(prev =>
      prev.some(item => item.value === opt.value)
        ? prev.filter(item => item.value !== opt.value)
        : [...prev, opt]
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {options.map(opt => (
          <Chip
            key={String(opt.value)}
            label={opt.label}
            selected={selected.some(item => item.value === opt.value)}
            disabled={disabled}
            onClick={() => toggle(opt)}
          />
        ))}
      </div>
      <Button
        type="button"
        size="sm"
        className="self-start"
        disabled={disabled || selected.length === 0}
        onClick={() =>
          onAnswer(
            question.question_id,
            selected.map(item => item.value),
            selected.map(item => item.label).join(', ')
          )
        }
      >
        확인
      </Button>
    </div>
  );
}

function normalizeTreatmentGroup(value: string) {
  return value
    .replace(/\s*\([^)]*\)\s*/g, '')
    .replace(/\s*치료$/g, '')
    .trim();
}

function getOptionTreatmentGroup(option: NormalizedOption, treatmentTypes: TreatmentType[]) {
  const optionValue = String(option.value);
  const matched = treatmentTypes.find(type => type.code === optionValue);
  return matched?.ui_group || normalizeTreatmentGroup(option.label);
}

function getTreatmentsByGroup(group: string, treatmentTypes: TreatmentType[]) {
  return treatmentTypes.filter(type => {
    if (type.active === false) {
      return false;
    }
    return normalizeTreatmentGroup(type.ui_group ?? '기타') === normalizeTreatmentGroup(group);
  });
}

function isNoTreatmentOption(option: NormalizedOption) {
  return option.value === 'NONE';
}

function TreatmentItemPrompt({ question, onAnswer, disabled }: InnerProps) {
  const options = normalizeOptions(question.options);
  const treatmentTypes = getActiveTreatmentTypes(question.treatment_types ?? []);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [selectedTreatments, setSelectedTreatments] = useState<
    Array<{ code: string; displayName: string }>
  >([]);
  const activeGroup =
    selectedGroup ?? (options[0] ? getOptionTreatmentGroup(options[0], treatmentTypes) : null);
  const groupTreatments = activeGroup ? getTreatmentsByGroup(activeGroup, treatmentTypes) : [];

  const toggleTreatment = (code: string, displayName: string) => {
    setSelectedTreatments(prev =>
      prev.some(item => item.code === code || item.displayName === displayName)
        ? prev.filter(item => item.code !== code && item.displayName !== displayName)
        : [...prev, { code, displayName }]
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {options.map(opt => {
          const group = getOptionTreatmentGroup(opt, treatmentTypes);
          const isNone = isNoTreatmentOption(opt);
          return (
            <ConfirmChip
              key={String(opt.value)}
              active={!isNone && activeGroup === group}
              variant={isNone ? 'toggle' : 'group'}
              className={isNone ? 'border-dashed text-muted' : 'px-4 py-2 text-sm font-semibold'}
              onClick={
                disabled
                  ? undefined
                  : () => {
                      if (isNone) {
                        onAnswer(question.question_id, [], opt.label);
                        return;
                      }
                      setSelectedGroup(group);
                    }
              }
            >
              {opt.label}
            </ConfirmChip>
          );
        })}
      </div>

      {activeGroup && (
        <div className="flex flex-col gap-2 border-t border-line/80 pt-3">
          <span className="text-xs font-bold text-muted">세부 치료 항목</span>
          <div className="flex flex-wrap gap-2">
            {groupTreatments.map(treatment => {
              const displayName = treatment.display_name || treatment.name || treatment.code;
              const selected = selectedTreatments.some(
                item => item.code === treatment.code || item.displayName === displayName
              );
              return (
                <ConfirmChip
                  key={treatment.code}
                  active={selected}
                  className="rounded-xl bg-white px-3.5 py-2 font-medium"
                  onClick={
                    disabled ? undefined : () => toggleTreatment(treatment.code, displayName)
                  }
                >
                  {selected && <Check aria-hidden="true" className="size-3.5" />}
                  <span>{displayName}</span>
                </ConfirmChip>
              );
            })}
          </div>
        </div>
      )}

      <Button
        type="button"
        size="sm"
        className="self-start"
        disabled={disabled || selectedTreatments.length === 0}
        onClick={() =>
          onAnswer(
            question.question_id,
            selectedTreatments.map(item => item.displayName),
            selectedTreatments.map(item => item.displayName).join(', ')
          )
        }
      >
        확인
      </Button>
    </div>
  );
}

function TextPrompt({ question, onAnswer, disabled }: InnerProps) {
  const [text, setText] = useState('');

  const submit = () => {
    const value = text.trim();
    if (!value) {
      return;
    }
    onAnswer(question.question_id, value, value);
    setText('');
  };

  return (
    <form
      className="flex gap-2"
      onSubmit={event => {
        event.preventDefault();
        submit();
      }}
    >
      <Input
        value={text}
        onChange={event => setText(event.target.value)}
        placeholder={question.placeholder ?? '입력해주세요'}
        disabled={disabled}
      />
      <Button type="submit" size="sm" disabled={disabled || !text.trim()}>
        전송
      </Button>
    </form>
  );
}

function FilePrompt({ question, onAnswer, disabled }: InnerProps) {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  return (
    <form
      className="flex max-w-full flex-col gap-3"
      onSubmit={event => {
        event.preventDefault();
        if (file) {
          onAnswer(question.question_id, file, file.name);
        }
      }}
    >
      <div className="flex max-w-full items-center gap-2">
        <Input
          ref={fileInputRef}
          type="file"
          className="sr-only"
          accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png"
          disabled={disabled}
          onChange={event => setFile(event.target.files?.[0] ?? null)}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload aria-hidden="true" />
          이미지 선택
        </Button>
        <span className="min-w-0 flex-1 truncate rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted">
          {file?.name ?? '선택된 이미지 없음'}
        </span>
      </div>
      <Button type="submit" size="sm" className="self-start" disabled={disabled || !file}>
        이미지 업로드
      </Button>
    </form>
  );
}
