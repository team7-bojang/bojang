import axios, { type InternalAxiosRequestConfig } from 'axios';

import { supabase } from '../lib/supabase';

// 401 재시도 여부를 표시하는 내부 플래그(무한 재시도 방지).
type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000',
  timeout: 30_000,
});

api.interceptors.request.use(async config => {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    } else {
      config.headers.Authorization = `Bearer test-token`;
    }
  } catch (error) {
    // Supabase 미작동 시 로컬 테스트용 더미 토큰 자동 주입
    console.warn('[API Auth] Session retrieval failed, using test token fallback:', error);
    config.headers.Authorization = `Bearer test-token`;
  }
  return config;
});

// 응답 401: 백그라운드 복귀 직후 등으로 access token이 잠깐 만료된 경우,
// 세션을 강제 갱신하고 원 요청을 1회만 재시도한다. (요청 인터셉터가 새 토큰을 재첨부)
api.interceptors.response.use(undefined, async error => {
  const config = error.config as RetriableConfig | undefined;
  if (error.response?.status === 401 && config && !config._retried) {
    config._retried = true;
    const { error: refreshError } = await supabase.auth.refreshSession();
    if (!refreshError) {
      return api(config);
    }
  }
  return Promise.reject(error);
});
