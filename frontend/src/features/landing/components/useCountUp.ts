import { useEffect, useRef, useState } from 'react';

/**
 * `active`가 true가 되면 0 → target까지 duration 동안 카운트업한다.
 * `instant`(reduce-motion 등)이면 즉시 target 값으로 고정.
 */
export function useCountUp(target: number, active: boolean, instant: boolean, durationMs = 1100) {
  // 애니메이션으로 증가하는 값. instant/비활성 시에는 렌더에서 직접 결정한다.
  const [animated, setAnimated] = useState(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    // instant이거나 비활성이면 애니메이션을 돌리지 않는다 (값은 렌더에서 결정).
    if (instant || !active) {
      return;
    }

    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      // easeOut(cubic)으로 룰렛 감속 느낌.
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimated(Math.round(target * eased));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };
    frameRef.current = requestAnimationFrame(tick);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [target, active, instant, durationMs]);

  if (instant) {
    return target;
  }
  if (!active) {
    return 0;
  }
  return animated;
}
