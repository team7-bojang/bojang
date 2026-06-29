import { useAuthModalStore } from './authModalStore';

const initialState = {
  isOpen: false,
  mode: 'login' as const,
  message: null,
};

beforeEach(() => {
  useAuthModalStore.setState(initialState);
});

describe('useAuthModalStore', () => {
  it('초기 상태는 닫혀 있고 login 모드다', () => {
    const state = useAuthModalStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.mode).toBe('login');
    expect(state.message).toBeNull();
  });

  it('openAuth: 기본값은 login 모드로 모달을 연다', () => {
    useAuthModalStore.getState().openAuth();
    const state = useAuthModalStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.mode).toBe('login');
    expect(state.message).toBeNull();
  });

  it('openAuth: 모드를 지정하면 해당 모드로 연다', () => {
    useAuthModalStore.getState().openAuth('signup');
    expect(useAuthModalStore.getState().mode).toBe('signup');
    expect(useAuthModalStore.getState().isOpen).toBe(true);
  });

  it('setMode: 모드를 바꾸고 message를 비운다', () => {
    useAuthModalStore.setState({ message: '안내 메시지' });
    useAuthModalStore.getState().setMode('signup');
    expect(useAuthModalStore.getState().mode).toBe('signup');
    expect(useAuthModalStore.getState().message).toBeNull();
  });

  it('switchToLoginWithMessage: 메시지와 함께 login 모달을 연다', () => {
    useAuthModalStore.getState().openAuth('signup');
    useAuthModalStore.getState().switchToLoginWithMessage('로그인이 필요합니다.');

    const state = useAuthModalStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.mode).toBe('login');
    expect(state.message).toBe('로그인이 필요합니다.');
  });

  it('close: 모달을 닫고 message를 비운다', () => {
    useAuthModalStore.getState().switchToLoginWithMessage('로그인이 필요합니다.');
    useAuthModalStore.getState().close();

    const state = useAuthModalStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.message).toBeNull();
  });
});
