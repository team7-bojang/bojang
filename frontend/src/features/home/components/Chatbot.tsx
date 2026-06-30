import { AnimatePresence, motion } from 'framer-motion';
import { Bot, Lock, SendHorizontal } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { QuestionPrompt } from '@/features/case/components/QuestionPrompt';
import { useChatFlow } from '@/features/case/hooks/useChatFlow';
import type { AnswerValue, ServiceType } from '@/features/case/model';
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

function BotAvatar() {
  return (
    <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
      <Bot className="size-5" />
    </span>
  );
}

function ChatbotThinking({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-3">
      <BotAvatar />
      <div className="flex items-center gap-3 rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-muted">
        <span>{text}</span>
        <span className="flex items-center gap-1" aria-label="진행 중" role="status">
          {[0, 1, 2].map(index => (
            <span
              key={index}
              className="size-1.5 animate-bounce rounded-full bg-primary"
              style={{ animationDelay: `${index * 120}ms` }}
            />
          ))}
        </span>
      </div>
    </div>
  );
}

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

  const handleTextInputRequest = useCallback(
    (request: { questionId: string; placeholder?: string }) => {
      const sourceQuestionId = pendingQuestion?.question_id;
      if (!sourceQuestionId) {
        return;
      }

      setComposerQuestionOverride(prev => {
        if (
          prev?.sourceQuestionId === sourceQuestionId &&
          prev.questionId === request.questionId &&
          prev.placeholder === request.placeholder
        ) {
          return prev;
        }

        return {
          sourceQuestionId,
          ...request,
        };
      });
    },
    [pendingQuestion?.question_id]
  );

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
        'flex flex-col rounded-card bg-surface px-6 py-4 shadow-sm ring-1 ring-line',
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
            <p className="text-sm font-semibold text-ink">먼저 가입한 보험을 선택해주세요</p>
            <p className="mt-1 text-sm leading-6 text-muted">
              그다음 챗봇에게 병원에 다녀온 상황을 편하게 알려주시면
              <br />
              보장을 확인해드려요.
            </p>
          </div>
        </div>
      ) : (
        <div
          ref={scrollRef}
          className="scrollbar-hide mt-3 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-1 pb-5 pt-3"
        >
          <motion.div
            className="flex items-start gap-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <BotAvatar />
            <p className="whitespace-pre-line rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-ink">
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
                  'max-w-[85%]',
                  message.role === 'user'
                    ? 'self-end rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm leading-6 text-white'
                    : 'self-start'
                )}
              >
                {message.role === 'user' ? (
                  message.text
                ) : (
                  <div className="flex items-start gap-3">
                    <BotAvatar />
                    <p className="whitespace-pre-line rounded-2xl rounded-tl-sm bg-canvas px-4 py-3 text-sm leading-6 text-ink">
                      {message.text}
                    </p>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {pendingQuestion && !done && !submitting && (
            <div className="ml-12 mt-1">
              <QuestionPrompt
                key={pendingQuestion.question_id}
                question={pendingQuestion}
                onAnswer={answer}
                onTextInputRequest={handleTextInputRequest}
                disabled={false}
              />
            </div>
          )}

          {submitting && (
            <ChatbotThinking
              text={started ? '입력을 확인하고 있습니다' : '답변을 분석하고 있습니다'}
            />
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
      )}

      <div className="shrink-0">
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
