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

export function AmountTiles({ amount }: { amount: number | null }) {
  if (amount === null) {
    // 금액 미입력: 숫자 타일 박스 안에 '-' 를 넣고 '원' 단위도 함께 표시한다.
    return (
      <div
        className="flex flex-wrap items-end justify-center gap-2 sm:gap-3"
        aria-label="산정 금액 없음"
      >
        <span className="amount-digit-tile">
          <span className="amount-digit-current">-</span>
        </span>
        <span className="pb-3 text-3xl font-black text-ink sm:pb-4">원</span>
      </div>
    );
  }

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
            <span className="pb-2 text-3xl font-black text-muted sm:pb-3">,</span>
          )}
        </div>
      ))}
      <span className="pb-3 text-3xl font-black text-ink sm:pb-4">원</span>
    </div>
  );
}
