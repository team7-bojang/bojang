import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

import { supabase } from '@/lib/supabase';

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

const initializedClients = new WeakSet<AxiosInstance>();

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

    if (error.response?.status === 401 && config && !config._retried) {
      config._retried = true;

      const { error: refreshError } = await supabase.auth.refreshSession();
      if (!refreshError) {
        return apiClient(config);
      }
    }

    return Promise.reject(error);
  });
}
