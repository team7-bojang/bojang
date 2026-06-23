import { createClient } from '@supabase/supabase-js';

import { Config } from '@/constants/config';

const url = Config.supabaseUrl;
const anonKey = Config.supabaseAnonKey;

if (!url || !anonKey) {
  console.warn(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY가 설정되지 않았습니다. 더미 Supabase 클라이언트를 초기화합니다.'
  );
}

const finalUrl = url || 'http://localhost:54321';
const finalKey = anonKey || 'dummy-anon-key-value-for-local-demo-without-supabase-instance';

export const supabase = createClient(finalUrl, finalKey);
