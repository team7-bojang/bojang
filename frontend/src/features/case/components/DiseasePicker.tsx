import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import type { AnswerValue, NextQuestion } from '../model';
import { normalizeOptions } from '../options';
import { Chip } from './Chip';

const PAGE_SIZE = 5;
const NONE_LABEL = '해당 병명이 없어요';
const DIRECT_INPUT_PLACEHOLDER = '질병명을 직접 입력해주세요';

interface DiseasePickerProps {
  question: NextQuestion;
  onAnswer: (questionId: string, value: AnswerValue, label: string) => void;
  onTextInputRequest?: (request: { questionId: string; placeholder: string }) => void;
  disabled?: boolean;
}

export function DiseasePicker({
  question,
  onAnswer,
  onTextInputRequest,
  disabled = false,
}: DiseasePickerProps) {
  const options = useMemo(() => normalizeOptions(question.options), [question.options]);
  const [page, setPage] = useState(0);
  const [directInput, setDirectInput] = useState(false);
  const [text, setText] = useState('');

  const start = page * PAGE_SIZE;
  const pageOptions = options.slice(start, start + PAGE_SIZE);
  const hasMore = start + PAGE_SIZE < options.length;

  const handleNone = () => {
    if (hasMore) {
      setPage(prev => prev + 1);
      return;
    }
    setDirectInput(true);
  };

  useEffect(() => {
    if (!directInput) {
      return;
    }

    onTextInputRequest?.({
      questionId: 'disease_name',
      placeholder: DIRECT_INPUT_PLACEHOLDER,
    });
  }, [directInput, onTextInputRequest]);

  if (directInput) {
    if (onTextInputRequest) {
      return null;
    }

    const submit = () => {
      const value = text.trim();
      if (!value) {
        return;
      }
      onAnswer('disease_name', value, value);
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
          placeholder={DIRECT_INPUT_PLACEHOLDER}
          disabled={disabled}
        />
        <Button type="submit" size="sm" disabled={disabled || !text.trim()}>
          전송
        </Button>
      </form>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {pageOptions.map(opt => (
        <Chip
          key={String(opt.value)}
          label={opt.label}
          disabled={disabled}
          onClick={() => onAnswer('disease_kcd', opt.value, opt.label)}
        />
      ))}
      <Chip label={NONE_LABEL} disabled={disabled} onClick={handleNone} />
    </div>
  );
}
