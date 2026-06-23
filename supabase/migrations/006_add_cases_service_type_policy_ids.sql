-- 004_alter_cases_columns.sql
-- cases 테이블에 CASE1/CASE2 분석 흐름 구분과
-- 이번 분석에 사용된 보험 목록을 저장하기 위한 컬럼 추가

ALTER TABLE public.cases
ADD COLUMN IF NOT EXISTS service_type text;

ALTER TABLE public.cases
ADD COLUMN IF NOT EXISTS policy_ids uuid[] DEFAULT ARRAY[]::uuid[];

-- service_type은 CASE1 또는 CASE2만 허용
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'cases_service_type_check'
    ) THEN
        ALTER TABLE public.cases
        ADD CONSTRAINT cases_service_type_check
        CHECK (
            service_type IS NULL
            OR service_type IN ('CASE1', 'CASE2')
        );
    END IF;
END $$;

-- CASE1 / CASE2별 조회용 인덱스
CREATE INDEX IF NOT EXISTS idx_cases_service_type
ON public.cases (service_type);

-- policy_ids 배열 검색용 인덱스
CREATE INDEX IF NOT EXISTS idx_cases_policy_ids
ON public.cases
USING gin (policy_ids);

COMMENT ON COLUMN public.cases.service_type IS
'분석 흐름 구분값. CASE1=청구가능보험 찾기, CASE2=추가보장 비교';

COMMENT ON COLUMN public.cases.policy_ids IS
'이번 분석 세션에서 사용자가 선택한 보험 ID 목록. CASE1은 다중 선택 가능, CASE2는 1개만 저장';
