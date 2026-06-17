import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  console.warn(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY 가 설정되지 않았습니다. 더미 Supabase 클라이언트를 초기화합니다.'
  );
}

// url이나 key가 비어 있으면 supabase-js가 에러를 던지므로 더미 값을 사용
const finalUrl = url || 'http://localhost:54321';
const finalKey = anonKey || 'dummy-anon-key-value-for-local-demo-without-supabase-instance';

export const supabase = createClient(finalUrl, finalKey);
