import type { CSSProperties } from 'react';
import { useMemo } from 'react';

const EMOJI = '🥲';
const EMOJI_COUNT = 8;

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min);
}

export function FallingSadEmojis() {
  const emojis = useMemo(
    () =>
      Array.from({ length: EMOJI_COUNT }, () => ({
        emoji: EMOJI,
        left: randomBetween(2, 96),
        size: randomBetween(1.35, 2.35),
        delay: randomBetween(0, 3.8),
        duration: randomBetween(5.6, 8.8),
        startDrift: randomBetween(-28, 28),
        midDrift: randomBetween(-86, 86),
        endDrift: randomBetween(-52, 52),
        rotate: randomBetween(-42, 42),
      })),
    []
  );

  return (
    <div className="sad-emoji-rain font-tossface" aria-hidden="true">
      {emojis.map((item, index) => (
        <span
          key={index}
          className="sad-emoji-drop"
          style={
            {
              left: `${item.left}%`,
              fontSize: `${item.size}rem`,
              '--sad-delay': `${item.delay}s`,
              '--sad-duration': `${item.duration}s`,
              '--sad-drift-start': `${item.startDrift.toFixed(1)}px`,
              '--sad-drift-mid': `${item.midDrift.toFixed(1)}px`,
              '--sad-drift-end': `${item.endDrift.toFixed(1)}px`,
              '--sad-rotate': `${item.rotate.toFixed(1)}deg`,
            } as CSSProperties
          }
        >
          {item.emoji}
        </span>
      ))}
    </div>
  );
}
