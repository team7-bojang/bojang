import axios from 'axios'

import { supabase } from '../lib/supabase'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000',
  timeout: 30_000,
})

// 요청마다 Supabase 세션 토큰을 Authorization 헤더로 첨부
api.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})
