import { useEffect, useState, type ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

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

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={event => {
        event.preventDefault();
        if (file) {
          onAnswer(question.question_id, file, file.name);
        }
      }}
    >
      <Input
        type="file"
        accept="application/pdf,.pdf"
        disabled={disabled}
        onChange={event => setFile(event.target.files?.[0] ?? null)}
      />
      <Button type="submit" size="sm" className="self-start" disabled={disabled || !file}>
        PDF 업로드
      </Button>
    </form>
  );
}
