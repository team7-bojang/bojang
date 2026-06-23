import { AnimatePresence, motion } from 'framer-motion';
import { Bot, Lock, SendHorizontal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { QuestionPrompt } from '@/features/case/components/QuestionPrompt';
import type { AnswerValue, ServiceType } from '@/features/case/model';
import { useChatFlow } from '@/features/case/hooks/useChatFlow';
import { cn } from '@/lib/utils';

const GREETING = '안녕하세요. 어떤 사고나 치료가 있었는지 먼저 알려주세요.';

interface ChatbotProps {
  className?: string;
  /** 전제 조건 미충족 시 입력 잠금. */
  locked?: boolean;
  /** 선택한 보험 상품 id. `/cases` 생성 요청의 policy_ids로 전달한다. */
  selectedPolicyIds: string[];
  serviceType: ServiceType;
  /** 최초 케이스 생성 완료 후 상위 화면에 선택 상태를 공유한다. */
  onCaseCreated?: (caseId: string, selectedPolicyIds: string[]) => void;
  /** 챗봇 수집이 끝난 뒤 확인 화면으로 이동하기 위한 콜백. */
  onDone?: (caseId: string) => void;
}

/** 상황 입력 후 질병 후보 확인과 후속 질문을 이어가는 챗봇. */
export function Chatbot({
  className,
  locked = false,
  selectedPolicyIds,
  serviceType,
  onCaseCreated,
  onDone,
}: ChatbotProps) {
  const { messages, caseId, pendingQuestion, submitting, error, done, start, answer } = useChatFlow(
    { serviceType, selectedPolicyIds, onCaseCreated, onDone }
  );
  const [input, setInput] = useState('');
  const [composerQuestionOverride, setComposerQuestionOverride] = useState<{
    sourceQuestionId: string;
    questionId: string;
    placeholder?: string;
  } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, pendingQuestion, submitting, error]);

  const started = caseId !== null;
  const pendingTextQuestion =
    pendingQuestion?.input_type === 'text_input'
      ? {
          questionId: pendingQuestion.question_id,
          placeholder: pendingQuestion.placeholder,
        }
      : null;
  const composerQuestion =
    composerQuestionOverride?.sourceQuestionId === pendingQuestion?.question_id
      ? composerQuestionOverride
      : pendingTextQuestion;
  const composerPlaceholder = composerQuestion?.placeholder ?? '답변을 입력해주세요';
  const inputDisabled = locked || submitting || (started && !composerQuestion);

  const handleSend = () => {
    if (inputDisabled) {
      return;
    }

    const value = input.trim();
    if (!value) {
      return;
    }

    setInput('');
    if (composerQuestion && caseId) {
      void answer(composerQuestion.questionId, value as AnswerValue, value);
      return;
    }

    void start(value);
  };

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6',
        className
      )}
    >
      <h2 className="shrink-0 text-lg font-bold text-ink">챗봇</h2>

      {locked && messages.length === 0 ? (
        <div className="mt-5 flex min-h-0 flex-1 flex-col items-center justify-center gap-3 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-canvas text-muted">
            <Lock className="size-6" />
          </span>
          <div>
            <p className="text-sm font-semibold text-ink">먼저 분석할 보험을 선택해주세요</p>
            <p className="mt-1 text-sm leading-6 text-muted">
              보험을 선택하거나 약관 PDF를 올리면
              <br />
              상황 입력을 시작할 수 있어요.
            </p>
          </div>
        </div>
      ) : (
        <div
          ref={scrollRef}
          className="scrollbar-hide mt-5 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto"
        >
          <motion.div
            className="flex items-start gap-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
              <Bot className="size-5" />
            </span>
            <p className="rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-ink">
              {GREETING}
            </p>
          </motion.div>

          <AnimatePresence initial={false}>
            {messages.map((message, index) => (
              <motion.div
                key={`${message.role}-${index}`}
                layout
                initial={{ opacity: 0, y: 10, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 500, damping: 32 }}
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6',
                  message.role === 'user'
                    ? 'self-end rounded-tr-sm bg-primary text-white'
                    : 'self-start rounded-tl-sm bg-canvas text-ink'
                )}
              >
                {message.text}
              </motion.div>
            ))}
          </AnimatePresence>

          {pendingQuestion && !done && (
            <div className="mt-1">
              <QuestionPrompt
                key={pendingQuestion.question_id}
                question={pendingQuestion}
                onAnswer={answer}
                onTextInputRequest={request => {
                  setComposerQuestionOverride({
                    sourceQuestionId: pendingQuestion.question_id,
                    ...request,
                  });
                }}
                disabled={submitting}
              />
            </div>
          )}

          {submitting && (
            <p className="self-start rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-muted">
              입력해주신 내용을 분석하고 있습니다.
            </p>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
      )}

      <div className="mt-6 shrink-0">
        <form
          className="relative"
          onSubmit={event => {
            event.preventDefault();
            handleSend();
          }}
        >
          <Input
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder={
              locked
                ? '보험을 먼저 선택해주세요'
                : composerQuestion
                  ? composerPlaceholder
                  : started
                    ? '아래 선택지에서 답해주세요'
                    : '상황을 입력해주세요'
            }
            className="pr-12"
            disabled={inputDisabled}
          />
          <Button
            type="submit"
            variant="ghost"
            size="icon"
            disabled={inputDisabled}
            className="absolute right-1 top-1/2 size-9 -translate-y-1/2 text-primary hover:bg-primary-tint"
            aria-label="메시지 전송"
          >
            <SendHorizontal />
          </Button>
        </form>
        <p className="mt-3 text-center text-xs leading-5 text-muted">
          AI 챗봇의 답변은 참고용이며, 실제 보장 여부는 약관과 상황에 따라 달라질 수 있습니다.
        </p>
      </div>
    </section>
  );
}
