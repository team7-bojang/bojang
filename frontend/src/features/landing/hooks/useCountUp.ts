import { useEffect, useRef, useState } from 'react';

interface AnimationState {
  key: string | null;
  value: number;
}

/**
 * `active`가 true가 되면 0 → target까지 duration 동안 카운트업한다.
 * `instant`(reduce-motion 등)이면 즉시 target 값으로 고정.
 */
export function useCountUp(
  target: number,
  active: boolean,
  instant: boolean,
  durationMs = 1100,
  resetKey = 'default'
) {
  // 애니메이션으로 증가하는 값. instant/비활성 시에는 렌더에서 직접 결정한다.
  const [animation, setAnimation] = useState<AnimationState>({ key: null, value: 0 });
  const frameRef = useRef<number | null>(null);
  const activeKey = `${resetKey}-${target}-${durationMs}`;

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
      setAnimation({ key: activeKey, value: Math.round(target * eased) });
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
  }, [target, active, instant, durationMs, activeKey]);

  if (instant) {
    return target;
  }
  if (!active) {
    return 0;
  }
  if (animation.key !== activeKey) {
    return 0;
  }
  return animation.value;
}
