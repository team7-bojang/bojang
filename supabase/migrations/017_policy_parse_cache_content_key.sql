-- 017_policy_parse_cache_content_key.sql
-- 동일 PDF(pdf_hash 동일)를 다른 사용자가 업로드한 경우에도 이미 끝난 온디맨드 LLM 파싱
-- 결과를 재사용하기 위한 공유 캐시 조회 키.
-- content_key = policies.pdf_hash (있으면) 없으면 policy_id 그대로 (기존 동작 유지).
-- 소유: 진미경

ALTER TABLE public.policy_parse_cache
    ADD COLUMN IF NOT EXISTS content_key text;

COMMENT ON COLUMN public.policy_parse_cache.content_key IS
    '공유 캐시 조회 키. policies.pdf_hash 존재 시 그 값, 없으면 policy_id. '
    '동일 PDF를 다른 사용자가 올려도 같은 content_key+query_hash로 매칭되어 LLM 재호출을 건너뛴다.';

-- 조회 패턴: 동일 content_key+query_hash로 이미 파싱된 다른 policy_id 찾기 (user_policy_service.get_or_parse_riders)
CREATE INDEX IF NOT EXISTS policy_parse_cache_content_key_query_hash_idx
    ON public.policy_parse_cache (content_key, query_hash);
