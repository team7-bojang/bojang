import { cn } from '@/lib/utils';
import { INSURERS, type InsurerId } from '../data/insurers';

interface InsurerLogoProps {
  insurerId: InsurerId;
  /** 컨테이너 크기 (기본 md). */
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses: Record<NonNullable<InsurerLogoProps['size']>, string> = {
  sm: 'size-10 p-1.5',
  md: 'size-12 p-2',
  lg: 'size-14 p-2.5',
};

/**
 * 로고 이미지 컨테이너.
 * 고정 크기 컨테이너를 먼저 그리고, 그 안에서 로고가 full(object-contain)로 채워진다.
 */
export function InsurerLogo({ insurerId, size = 'md', className }: InsurerLogoProps) {
  const insurer = INSURERS[insurerId];

  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center overflow-hidden rounded-xl border border-line bg-surface',
        sizeClasses[size],
        className
      )}
    >
      <img
        src={insurer.logo}
        alt={`${insurer.name} 로고`}
        className="h-full w-full object-contain"
      />
    </div>
  );
}
