-- 010_riders_parse_query_hash.sql
-- riders 테이블에 parse_query_hash 컬럼 추가.
-- 온디맨드 파싱 시 어떤 입력 조합으로 생성된 rider인지 추적하기 위해 사용.
-- 동일 policy에 대해 다른 시나리오(질병+처치)로 파싱한 riders가 섞이지 않도록 한다.
-- 소유: 진미경

ALTER TABLE public.riders
    ADD COLUMN IF NOT EXISTS parse_query_hash text;

-- 온디맨드 파싱 riders 조회 패턴: policy_id + hash 복합 인덱스
CREATE INDEX IF NOT EXISTS riders_policy_parse_hash_idx
    ON public.riders (policy_id, parse_query_hash);

COMMENT ON COLUMN public.riders.parse_query_hash IS
    '온디맨드 파싱 시 입력값(policy_id+kcd+treatment_items+visit_type+surgery)의 MD5 해시. '
    'NULL이면 스크립트 사전파싱(scripts/parsing) 또는 preset 복제로 생성된 rider.';
