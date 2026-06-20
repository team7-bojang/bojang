import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

import { formatWon } from '../utils/format';

function RollingDigit({ digit, order }: { digit: string; order: number }) {
  const targetDigit = Number(digit);
  const [displayDigit, setDisplayDigit] = useState((targetDigit + order + 7) % 10);
  const [rolling, setRolling] = useState(true);

  useEffect(() => {
    let tick = 0;
    const maxTicks = 18 + order * 2;

    const intervalId = window.setInterval(() => {
      tick += 1;
      setDisplayDigit((targetDigit + tick + order * 3) % 10);

      if (tick >= maxTicks) {
        window.clearInterval(intervalId);
        setDisplayDigit(targetDigit);
        setRolling(false);
      }
    }, 38);

    return () => window.clearInterval(intervalId);
  }, [order, targetDigit]);

  return (
    <span className="amount-digit-tile">
      <span className={cn('amount-digit-current', rolling && 'amount-digit-current-rolling')}>
        {displayDigit}
      </span>
    </span>
  );
}

export function AmountTiles({ amount }: { amount: number }) {
  const value = amount.toString();
  const groups = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',').split(',');

  return (
    <div
      className="flex flex-wrap items-end justify-center gap-2 sm:gap-3"
      aria-label={`${formatWon(amount)}원`}
    >
      {groups.map((group, groupIndex) => (
        <div key={`${group}-${groupIndex}`} className="flex items-end gap-1.5 sm:gap-2">
          {group.split('').map((digit, digitIndex) => {
            const order = groupIndex * 3 + digitIndex;

            return <RollingDigit key={`${groupIndex}-${digitIndex}`} digit={digit} order={order} />;
          })}
          {groupIndex < groups.length - 1 && (
            <span className="pb-2 text-3xl font-black text-muted sm:pb-3 sm:text-5xl">,</span>
          )}
        </div>
      ))}
      <span className="pb-3 text-2xl font-black text-ink sm:pb-4 sm:text-4xl">원</span>
    </div>
  );
}
