import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

import { useAuthModalStore } from '@/features/auth/store/authModalStore';
import { supabase } from '@/lib/supabase';

type RetriableConfig = InternalAxiosRequestConfig & {
  _retried?: boolean;
  _loginRetried?: boolean;
};

const initializedClients = new WeakSet<AxiosInstance>();
const UNAUTHORIZED_MESSAGE = '로그인이 필요합니다. 다시 로그인해주세요.';
let loginRequiredPromise: Promise<void> | null = null;

async function waitForLoginAfterUnauthorized() {
  if (loginRequiredPromise) {
    return loginRequiredPromise;
  }

  useAuthModalStore.getState().switchToLoginWithMessage(UNAUTHORIZED_MESSAGE);

  loginRequiredPromise = new Promise<void>((resolve, reject) => {
    let unsubscribeAuth: { data: { subscription: { unsubscribe: () => void } } } | null = null;
    let unsubscribeModal: (() => void) | null = null;
    let settled = false;

    const cleanup = () => {
      unsubscribeAuth?.data.subscription.unsubscribe();
      unsubscribeModal?.();
      loginRequiredPromise = null;
    };

    const resolveAfterLogin = () => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      resolve();
    };

    const rejectAfterClose = () => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      reject(new Error('로그인이 취소되었습니다.'));
    };

    void supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        resolveAfterLogin();
      }
    });

    unsubscribeAuth = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        resolveAfterLogin();
      }
    });

    unsubscribeModal = useAuthModalStore.subscribe(state => {
      if (!state.isOpen) {
        void supabase.auth.getSession().then(({ data }) => {
          if (data.session) {
            resolveAfterLogin();
            return;
          }

          rejectAfterClose();
        });
      }
    });
  });

  return loginRequiredPromise;
}

/**
 * 인증이 필요한 axios 인스턴스에 공통 인터셉터를 등록한다.
 *
 * - 요청 전 Supabase 세션의 access token을 Authorization 헤더에 주입한다.
 * - 401 응답이 오면 세션을 한 번 refresh한 뒤 원 요청을 한 번만 재시도한다.
 * - React StrictMode나 중복 초기화로 같은 인스턴스에 인터셉터가 여러 번 붙지 않도록 막는다.
 */
export function setupHttpInterceptors(apiClient: AxiosInstance) {
  if (initializedClients.has(apiClient)) {
    return;
  }

  initializedClients.add(apiClient);

  apiClient.interceptors.request.use(async config => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      config.headers.Authorization = `Bearer ${session?.access_token ?? 'test-token'}`;
    } catch (error) {
      console.warn('[API Auth] 세션 조회 실패, 테스트 토큰으로 대체합니다:', error);
      config.headers.Authorization = 'Bearer test-token';
    }

    return config;
  });

  apiClient.interceptors.response.use(undefined, async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;

    if (error.response?.status !== 401) {
      // 서버가 보낸 error.message 추출 (success: false 봉투 구조)
      const body = error.response?.data as Record<string, unknown> | undefined;
      if (body && body['success'] === false) {
        const msg = (body['error'] as { message?: string } | undefined)?.message;
        if (msg) {
          return Promise.reject(new Error(msg));
        }
      }
      return Promise.reject(error);
    }

    if (config && !config._retried) {
      config._retried = true;

      const { data, error: refreshError } = await supabase.auth.refreshSession();
      if (!refreshError && data.session) {
        return apiClient(config);
      }
    }

    // 재로그인 후에도 401이 반복되면 무한 재시도가 되므로, 이 경로도 1회로 제한한다.
    if (config && !config._loginRetried) {
      config._loginRetried = true;
      await waitForLoginAfterUnauthorized();
      return apiClient(config);
    }

    return Promise.reject(error);
  });
}
