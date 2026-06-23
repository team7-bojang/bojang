-- 009_policy_parse_cache.sql
-- 온디맨드 파싱 결과 캐시 테이블.
-- (policy_id, query_hash) 단위로 캐시하여 동일 입력 반복 파싱을 방지한다.
-- query_hash = md5(policy_id + disease_kcd + treatment_items + visit_type + surgery)
-- 소유: 진미경

CREATE TABLE IF NOT EXISTS public.policy_parse_cache (
    id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    policy_id   uuid        NOT NULL REFERENCES public.policies(id) ON DELETE CASCADE,
    query_hash  text        NOT NULL,
    created_at  timestamptz DEFAULT now(),
    -- 동일 (policy, 입력조합) 캐시 중복 방지
    UNIQUE (policy_id, query_hash)
);

CREATE INDEX IF NOT EXISTS policy_parse_cache_policy_id_idx
    ON public.policy_parse_cache (policy_id);

-- RLS: 본인 policy의 캐시만 접근 가능
ALTER TABLE public.policy_parse_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "parse_cache_owner_select"
    ON public.policy_parse_cache FOR SELECT
    USING (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "parse_cache_owner_insert"
    ON public.policy_parse_cache FOR INSERT
    WITH CHECK (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "parse_cache_owner_delete"
    ON public.policy_parse_cache FOR DELETE
    USING (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

COMMENT ON TABLE public.policy_parse_cache IS
    '온디맨드 파싱 캐시. (policy_id, query_hash) 단위로 LLM 재파싱 방지.';
COMMENT ON COLUMN public.policy_parse_cache.query_hash IS
    'md5(policy_id + disease_kcd + treatment_items + visit_type + surgery). 동일 입력 = 동일 해시.';
