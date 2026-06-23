import { cn } from '@/lib/utils';
import type { CSSProperties } from 'react';

export function FireworkBurst({ className, delay = 0 }: { className?: string; delay?: number }) {
  const sparks = Array.from({ length: 34 }, (_, index) => {
    const angle = (Math.PI * 2 * index) / 34;
    const radius = index % 3 === 0 ? 72 : index % 3 === 1 ? 58 : 44;

    return {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      rotate: (angle * 180) / Math.PI,
    };
  });

  return (
    <div
      className={cn('firework', className)}
      style={{ '--firework-delay': `${delay}s` } as CSSProperties}
      aria-hidden="true"
    >
      <span className="firework-launch" />
      {sparks.map((spark, index) => (
        <span
          key={index}
          className="firework-spark"
          style={
            {
              '--spark-x': `${spark.x.toFixed(2)}px`,
              '--spark-y': `${spark.y.toFixed(2)}px`,
              '--spark-rotate': `${spark.rotate.toFixed(2)}deg`,
              '--spark-delay': `${delay + (index % 3) * 0.006}s`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}
