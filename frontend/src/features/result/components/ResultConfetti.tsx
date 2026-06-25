import type { CSSProperties } from 'react';

type ConfettiSide = 'left' | 'right';

const PIECES = [
  { side: 'left', x: -124, y: -84, rotate: -42, delay: 0, color: '#facc15', shape: 'rounded-sm' },
  { side: 'left', x: -98, y: -122, rotate: 20, delay: 24, color: '#0ea5e9', shape: 'rounded-sm' },
  { side: 'left', x: -72, y: -70, rotate: -64, delay: 54, color: '#f43f5e', shape: 'rounded-full' },
  { side: 'left', x: -46, y: -138, rotate: 34, delay: 12, color: '#14b8a6', shape: 'rounded-sm' },
  { side: 'left', x: -140, y: -28, rotate: 58, delay: 70, color: '#f43f5e', shape: 'rounded-sm' },
  { side: 'left', x: -92, y: -12, rotate: -74, delay: 86, color: '#facc15', shape: 'rounded-full' },
  { side: 'left', x: -42, y: -34, rotate: 72, delay: 104, color: '#0ea5e9', shape: 'rounded-sm' },
  { side: 'right', x: 46, y: -132, rotate: 42, delay: 18, color: '#f43f5e', shape: 'rounded-sm' },
  { side: 'right', x: 76, y: -78, rotate: -34, delay: 68, color: '#0ea5e9', shape: 'rounded-sm' },
  {
    side: 'right',
    x: 104,
    y: -118,
    rotate: 24,
    delay: 36,
    color: '#facc15',
    shape: 'rounded-full',
  },
  { side: 'right', x: 132, y: -56, rotate: 58, delay: 60, color: '#14b8a6', shape: 'rounded-sm' },
  { side: 'right', x: 42, y: -28, rotate: -56, delay: 76, color: '#f43f5e', shape: 'rounded-sm' },
  { side: 'right', x: 92, y: -12, rotate: 36, delay: 96, color: '#14b8a6', shape: 'rounded-full' },
  { side: 'right', x: 138, y: -20, rotate: -26, delay: 112, color: '#facc15', shape: 'rounded-sm' },
] as const;

export function ResultConfetti({ side }: { side: ConfettiSide }) {
  const pieces = PIECES.filter(piece => piece.side === side);

  return (
    <span className={`result-confetti result-confetti-${side}`} aria-hidden="true">
      {pieces.map((piece, index) => (
        <span
          key={index}
          className={`result-confetti-piece ${piece.shape}`}
          style={
            {
              '--confetti-x': `${piece.x}px`,
              '--confetti-y': `${piece.y}px`,
              '--confetti-rotate': `${piece.rotate}deg`,
              '--confetti-delay': `${piece.delay}ms`,
              '--confetti-color': piece.color,
            } as CSSProperties
          }
        />
      ))}
    </span>
  );
}
