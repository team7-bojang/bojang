import axios from 'axios';

import { supabase } from '../lib/supabase';

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
