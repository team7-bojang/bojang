import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import { AUTH_COPY } from '@/features/auth/constants';
import { AuthForm } from '@/features/auth/components/AuthForm';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';

export function AuthModal() {
  const isOpen = useAuthModalStore(state => state.isOpen);
  const mode = useAuthModalStore(state => state.mode);
  const close = useAuthModalStore(state => state.close);

  const copy = AUTH_COPY[mode];

  return (
    <Dialog.Root
      open={isOpen}
      onOpenChange={isOpen => {
        if (!isOpen) {
          close();
        }
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-card bg-surface p-6 shadow-xl ring-1 ring-line focus:outline-none sm:p-7">
          <Dialog.Title className="sr-only">{copy.title}</Dialog.Title>
          <Dialog.Description className="sr-only">{copy.description}</Dialog.Description>
          <Dialog.Close
            className="absolute right-4 top-4 flex size-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-canvas hover:text-ink"
            aria-label="닫기"
          >
            <X className="size-4" />
          </Dialog.Close>
          {/* key={mode}: 모드 전환 시 폼·에러 상태 완전 초기화 */}
          <AuthForm key={mode} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
