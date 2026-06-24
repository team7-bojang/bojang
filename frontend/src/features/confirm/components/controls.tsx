import { Lock } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';

/** 필수 표시(*) 마커. */
export function Required() {
  return <span className="ml-0.5 text-orange-500">*</span>;
}

/** 라벨 + 필드 래퍼. */
export function Field({
  label,
  required,
  hint,
  locked,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: React.ReactNode;
  locked?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="flex items-center gap-1 text-sm font-bold text-ink">
        {label}
        {required && <Required />}
        {hint}
        {locked && <Lock className="size-3.5 text-muted" />}
      </label>
      {children}
    </div>
  );
}

/** 칩 토글 버튼 (복수 선택). */
export function Chip({
  active,
  onClick,
  size = 'md',
  variant = 'toggle',
  className,
  children,
}: {
  active?: boolean;
  onClick?: () => void;
  size?: 'sm' | 'md';
  variant?: 'toggle' | 'solid' | 'group';
  className?: string;
  children: React.ReactNode;
}) {
  const interactive = Boolean(onClick);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!interactive}
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-full border transition-colors disabled:cursor-default',
        size === 'sm' ? 'px-2.5 py-1 text-xs font-medium' : 'px-3.5 py-2 text-sm font-medium',
        variant === 'solid'
          ? 'border-primary bg-primary text-white'
          : active
            ? 'border-primary bg-primary-tint text-ink-deep'
            : 'border-line bg-white text-ink',
        variant === 'group' && active && 'border-primary bg-primary text-white',
        interactive && !active && 'hover:border-primary/40',
        className
      )}
    >
      {children}
    </button>
  );
}

/** 숫자 입력 + 단위 접미사 (음수 불가). */
export function NumberField({
  value,
  onChange,
  placeholder,
  suffix,
  disabled,
}: {
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder?: string;
  suffix: string;
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <Input
        type="number"
        inputMode="numeric"
        min={0}
        disabled={disabled}
        value={value ?? ''}
        placeholder={placeholder}
        onKeyDown={event => {
          // 음수/지수 입력 차단.
          if (['-', 'e', 'E', '+'].includes(event.key)) {
            event.preventDefault();
          }
        }}
        onChange={event => {
          const raw = event.target.value;
          onChange(raw === '' ? null : Math.max(0, Number(raw)));
        }}
        className="pr-10"
      />
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted">
        {suffix}
      </span>
    </div>
  );
}
