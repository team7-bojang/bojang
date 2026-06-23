import { cn } from '@/lib/utils';

interface ChipProps {
  label: string;
  selected?: boolean;
  disabled?: boolean;
  onClick: () => void;
}

export function Chip({ label, selected = false, disabled = false, onClick }: ChipProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'rounded-2xl px-4 py-2 text-sm font-medium ring-1 transition-colors disabled:opacity-50',
        selected
          ? 'bg-primary text-white ring-primary'
          : 'bg-canvas text-ink ring-line hover:bg-primary-tint'
      )}
    >
      {label}
    </button>
  );
}
