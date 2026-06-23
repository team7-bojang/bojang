import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';

import { cn } from '@/lib/utils';
import { useCountUp } from '@/features/landing/components/useCountUp';

type CaseKey = 'case1' | 'case2';
type StepKey = 'home' | 'confirm' | 'result';

const STEP_ORDER: StepKey[] = ['home', 'confirm', 'result'];

// 결과 단계는 연출을 보여줄 수 있게 더 길게 머문다.
const STEP_HOLD_MS: Record<StepKey, number> = {
  home: 3400,
  confirm: 2600,
  result: 4000,
};

// 케이스별 탭 정의.
const CASES: { key: CaseKey; label: string }[] = [
  { key: 'case1', label: '청구가능' },
  { key: 'case2', label: '추가보장찾기' },
];

// 케이스별 홈 단계 타이핑 질문.
const TYPING_TARGET: Record<CaseKey, string> = {
  case1: '허리디스크로 입원했어요. 청구가 가능할까요?',
  case2: '받을 수 있는 보장을 더 찾고 싶어요.',
};

const TYPING_SPEED_MS = 55;

const STEP_LABEL: Record<StepKey, string> = {
  home: '1 · 상황 입력',
  confirm: '2 · 상황 확인',
  result: '3 · 분석 결과',
};

// Case1 금액, Case2 그래프 수치 (실제 mock 톤에 맞춘 예시값).
const PAYABLE_AMOUNT = 612000;
const CURRENT_AMOUNT = 480000;
const EXPECTED_AMOUNT = 760000;

function formatWon(value: number) {
  return value.toLocaleString('ko-KR');
}

/** 히어로 우측: 탭으로 케이스를 골라 그 흐름(입력→확인→결과)을 미니 UI로 순환 재현. */
export function HeroFlowAnimation({ className }: { className?: string }) {
  const reduceMotion = useReducedMotion() ?? false;
  const [caseKey, setCaseKey] = useState<CaseKey>('case1');
  // 단계 진행은 콘텐츠 전달이므로 항상 홈부터 순환한다.
  // (reduce-motion은 전환·카운트업·막대 상승 같은 장식 모션만 제거)
  const [stepIndex, setStepIndex] = useState(0);
  // 홈 단계 타자기 효과: 표시할 글자 수만 상태로 두고 텍스트는 렌더에서 slice.
  const [typedCount, setTypedCount] = useState(reduceMotion ? TYPING_TARGET.case1.length : 0);
  // step/caseKey가 바뀌면 렌더 중에 글자 수를 리셋한다 (effect 내 동기 setState 회피).
  const [typingKey, setTypingKey] = useState('case1-home');

  const step = STEP_ORDER[stepIndex];
  const currentTypingKey = `${caseKey}-${step}`;
  if (typingKey !== currentTypingKey) {
    setTypingKey(currentTypingKey);
    setTypedCount(reduceMotion ? TYPING_TARGET[caseKey].length : 0);
  }

  const typed = TYPING_TARGET[caseKey].slice(0, typedCount);

  // 금액 카운트업 (case1 결과 단계 진입 시 동작).
  const payable = useCountUp(
    PAYABLE_AMOUNT,
    caseKey === 'case1' && step === 'result',
    reduceMotion
  );

  // 탭 변경 시 흐름을 홈부터 재시작. (타자기 글자 수는 위 렌더 리셋에서 처리)
  const selectCase = (next: CaseKey) => {
    setCaseKey(next);
    setStepIndex(0);
  };

  // 단계 자동 순환. 단계별 체류 시간이 다르므로 setTimeout 체인.
  // (reduce-motion이어도 흐름 전달을 위해 순환은 유지 — 장식 모션만 아래에서 제거)
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setStepIndex(prev => (prev + 1) % STEP_ORDER.length);
    }, STEP_HOLD_MS[step]);
    return () => window.clearTimeout(timer);
  }, [step, caseKey]);

  // 홈 단계 진입 시 타자기 효과 (케이스별 질문).
  useEffect(() => {
    if (reduceMotion || step !== 'home') {
      return;
    }
    const target = TYPING_TARGET[caseKey];
    let i = 0;
    const timer = window.setInterval(() => {
      i += 1;
      setTypedCount(i);
      if (i >= target.length) {
        window.clearInterval(timer);
      }
    }, TYPING_SPEED_MS);
    return () => window.clearInterval(timer);
  }, [step, caseKey, reduceMotion]);

  // Case2 그래프 막대 비율.
  const currentRatio = (CURRENT_AMOUNT / EXPECTED_AMOUNT) * 100;
  const addedRatio = 100 - currentRatio;

  return (
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-card bg-surface p-5 shadow-lg ring-1 ring-line',
        className
      )}
    >
      {/* 케이스 선택 탭 */}
      <div className="mb-4 flex gap-1 rounded-xl bg-primary-tint/30 p-1">
        {CASES.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => selectCase(key)}
            className={cn(
              'flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition-colors',
              caseKey === key ? 'bg-surface text-primary shadow-sm' : 'text-muted hover:text-ink'
            )}
            aria-pressed={caseKey === key}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mb-4 flex items-center gap-2 text-xs font-semibold text-primary">
        <span className="font-tossface">✨</span>
        {STEP_LABEL[step]}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${caseKey}-${step}`}
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="min-h-65"
        >
          {step === 'home' && (
            <div className="flex flex-col gap-3">
              <div className="flex items-start gap-2">
                <span className="font-tossface flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-tint text-base">
                  🤖
                </span>
                <p className="rounded-2xl rounded-tl-sm bg-primary-tint/40 px-3 py-2 text-xs leading-5 text-ink">
                  어떤 상황인지 편하게 적어주세요 🙂
                </p>
              </div>
              <div className="ml-auto max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-3 py-2 text-xs leading-5 text-white">
                {typed}
                <span className="ml-0.5 inline-block w-0.5 animate-pulse bg-white/80">&nbsp;</span>
              </div>
            </div>
          )}

          {step === 'confirm' && (
            <div className="flex flex-col gap-2">
              {[
                ['가입 보험', '○○생명 건강보험'],
                ['질병', '허리디스크 (M51)'],
                ['치료', '입원 8일'],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between rounded-xl border border-line bg-primary-tint/20 px-3 py-2 text-xs"
                >
                  <span className="text-muted">{label}</span>
                  <span className="font-semibold text-ink">{value}</span>
                </div>
              ))}
            </div>
          )}

          {/* 결과 — Case1: 청구 가능 보장 (금액 카운트업, 룰렛 느낌) */}
          {step === 'result' && caseKey === 'case1' && (
            <div className="flex flex-col gap-3">
              <div className="rounded-xl bg-primary-tint/30 px-4 py-4 text-center">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-success">
                  <span className="font-tossface">✅</span>
                  청구 가능 보장 2건을 찾았어요
                </div>
                <p className="mt-1 text-[11px] font-semibold text-muted">예상 보험금</p>
                <p className="mt-1 text-3xl font-black tabular-nums text-primary">
                  {formatWon(payable)}
                  <span className="ml-0.5 text-base font-black text-ink">원</span>
                </p>
              </div>
              {['입원일당 특약', '질병수술비 특약'].map(name => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded-xl border border-line px-3 py-2 text-xs"
                >
                  <span className="font-medium text-ink">{name}</span>
                  <span className="font-semibold text-primary">청구 가능</span>
                </div>
              ))}
            </div>
          )}

          {/* 결과 — Case2: 추가 보장 찾기 (성장 막대 그래프) */}
          {step === 'result' && caseKey === 'case2' && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-1.5 text-xs font-bold text-primary">
                <span className="font-tossface">📈</span>
                조건을 채우면 더 받을 수 있어요
              </div>
              <div className="flex items-end justify-center gap-6 rounded-xl bg-primary-tint/30 px-4 pb-3 pt-4">
                {/* 현재 막대 */}
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-32 items-end">
                    <motion.div
                      className="w-12 rounded-t-md bg-[#bfe5df]"
                      initial={reduceMotion ? false : { height: 0 }}
                      animate={{ height: `${(CURRENT_AMOUNT / EXPECTED_AMOUNT) * 8}rem` }}
                      transition={{ duration: 0.7, ease: 'easeOut' }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-muted">현재</span>
                  <span className="text-xs font-bold text-ink">{formatWon(CURRENT_AMOUNT)}원</span>
                </div>
                {/* 조건 충족 시 막대 (상단 추가분 강조) */}
                <div className="flex flex-col items-center gap-2">
                  <motion.div
                    className="flex w-12 flex-col-reverse overflow-hidden rounded-t-md"
                    initial={reduceMotion ? false : { height: 0 }}
                    animate={{ height: '8rem' }}
                    transition={{ duration: 0.7, ease: 'easeOut' }}
                  >
                    <div className="bg-[#bfe5df]" style={{ height: `${currentRatio}%` }} />
                    <div className="bg-[#18c9b5]" style={{ height: `${addedRatio}%` }} />
                  </motion.div>
                  <span className="text-[10px] font-semibold text-primary">조건 충족 시</span>
                  <span className="text-xs font-black text-primary">
                    {formatWon(EXPECTED_AMOUNT)}원
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* 단계 인디케이터 */}
      <div className="mt-4 flex gap-1.5">
        {STEP_ORDER.map((key, i) => (
          <span
            key={key}
            className={cn(
              'h-1.5 flex-1 rounded-full transition-colors',
              i === stepIndex ? 'bg-primary' : 'bg-line'
            )}
          />
        ))}
      </div>
    </div>
  );
}
