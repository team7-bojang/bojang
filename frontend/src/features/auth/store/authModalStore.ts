import { create } from 'zustand';

import type { AuthMode } from '@/features/auth/types';

interface AuthModalState {
  isOpen: boolean;
  mode: AuthMode;
  message: string | null;
  openAuth: (mode?: AuthMode) => void;
  setMode: (mode: AuthMode) => void;
  switchToLoginWithMessage: (message: string) => void;
  close: () => void;
}

export const useAuthModalStore = create<AuthModalState>(set => ({
  isOpen: false,
  mode: 'login',
  message: null,
  openAuth: (mode = 'login') => set({ isOpen: true, mode, message: null }),
  setMode: mode => set({ mode, message: null }),
  switchToLoginWithMessage: message => set({ isOpen: true, mode: 'login', message }),
  close: () => set({ isOpen: false, message: null }),
}));
