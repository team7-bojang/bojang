import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, Bot, ChevronRight, Lock, SendHorizontal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface ChatMessage {
  role: 'bot' | 'user';
  text: string;
}

const GREETING = '안녕하세요! 보장체크 AI 챗봇이에요 🙂 어떤 도움이 필요하신가요?';

const SUGGESTIONS = [
  '사고가 났을 때 보장 받을 수 있을까요?',
  '실비 보험 청구는 어떻게 하나요?',
  '특약에 대해 궁금해요',
];

interface ChatbotProps {
  className?: string;
  /** 전제 조건 미충족 시 입력 잠금 (보험 선택/ PDF 업로드 전). */
  locked?: boolean;
  /** 상황 확인 후 분석 시작(다음 페이지) 트리거. */
  onStartAnalysis?: () => void;
}

const CONFIRM_TEXT = '입력해주신 상황을 확인했어요. 이대로 분석을 시작할까요?';

/** "챗봇" — 추천 질문 칩 + 메시지 입력 (단순형). */
export function Chatbot({ className, locked = false, onStartAnalysis }: ChatbotProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // 사용자가 상황을 한 번이라도 입력하면 분석 시작을 안내.
  const hasUserInput = messages.some(message => message.role === 'user');

  // 새 메시지가 추가되면 항상 맨 아래로 스크롤 (사용자는 채팅 입력에만 집중).
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const send = (text: string) => {
    if (locked) {
      return;
    }
    const value = text.trim();
    if (!value) {
      return;
    }
    // TODO: 백엔드 챗봇 API 연동 — 현재는 입력만 누적.
    setMessages(prev => [...prev, { role: 'user', text: value }]);
    setInput('');
  };

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6',
        className
      )}
    >
      <h2 className="shrink-0 text-lg font-bold text-ink">챗봇</h2>

      {locked ? (
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
          {/* 봇 인사 */}
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

          {/* 추천 질문 */}
          <div className="flex flex-col gap-2">
            {SUGGESTIONS.map((suggestion, index) => (
              <motion.button
                key={suggestion}
                type="button"
                onClick={() => send(suggestion)}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 + index * 0.07 }}
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.99 }}
                className="flex items-center justify-between gap-2 rounded-2xl border border-line bg-surface px-4 py-3 text-left text-sm text-ink transition-colors hover:border-primary/40 hover:bg-primary-tint/40"
              >
                <span>{suggestion}</span>
                <ChevronRight className="size-4 shrink-0 text-muted" />
              </motion.button>
            ))}
          </div>

          {/* 대화 내역 */}
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

          {/* 상황 확인 후 분석 시작 */}
          <AnimatePresence>
            {hasUserInput && (
              <motion.div
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ type: 'spring', stiffness: 500, damping: 32 }}
                className="flex flex-col gap-3 self-start rounded-2xl rounded-tl-sm bg-canvas px-4 py-3"
              >
                <p className="text-sm leading-6 text-ink">{CONFIRM_TEXT}</p>
                <Button type="button" size="sm" className="self-start" onClick={onStartAnalysis}>
                  분석 시작
                  <ArrowRight />
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      <div className="mt-6 shrink-0">
        <form
          className="relative"
          onSubmit={event => {
            event.preventDefault();
            send(input);
          }}
        >
          <Input
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder={locked ? '보험을 먼저 선택해주세요' : '메시지를 입력하세요...'}
            className="pr-12"
            disabled={locked}
          />
          <Button
            type="submit"
            variant="ghost"
            size="icon"
            disabled={locked}
            className="absolute right-1 top-1/2 size-9 -translate-y-1/2 text-primary hover:bg-primary-tint"
            aria-label="메시지 전송"
          >
            <SendHorizontal />
          </Button>
        </form>
        <p className="mt-3 text-center text-xs leading-5 text-muted">
          ※ 챗봇의 답변은 참고용이며, 실제 보장 여부는 약관 및 상황에 따라 달라질 수 있습니다.
        </p>
      </div>
    </section>
  );
}
