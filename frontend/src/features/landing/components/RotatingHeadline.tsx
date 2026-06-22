import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';

import { cn } from '@/lib/utils';

const PHRASES = ['놓친 보장이 있는지', '받을 수 있는 보험금이 있는지', '청구 가능한 특약이 있는지'];

const INTERVAL_MS = 2500;

interface RotatingHeadlineProps {
  className?: string;
}

/** 히어로 제목 둘째 줄 — 문구 3개를 순환 표시. */
export function RotatingHeadline({ className }: RotatingHeadlineProps) {
  const reduceMotion = useReducedMotion();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (reduceMotion) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex(prev => (prev + 1) % PHRASES.length);
    }, INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [reduceMotion]);

  return (
    <span className={cn('relative block text-primary', className)}>
      {/* 스크린리더용 정적 라벨 (회전 문구는 장식이므로 읽지 않음). */}
      <span className="sr-only">놓친 보장이나 받을 수 있는 보험금이 있는지</span>
      <AnimatePresence mode="wait">
        <motion.span
          key={index}
          className="block"
          aria-hidden="true"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          {PHRASES[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
