-- 운영 Supabase 프로젝트 bojang의 public 스키마와 로컬 마이그레이션 정합화.
-- 기준 확인일: 2026-06-22
-- 운영 DB를 변경하기 위한 파일이 아니라, 새 환경에서 001~006 적용 후
-- 운영 프로젝트와 같은 최종 제약/RLS 상태를 재현하기 위한 후속 migration이다.

BEGIN;

ALTER TABLE public.cases
    DROP CONSTRAINT IF EXISTS cases_policy_elapsed_days_nonnegative;

ALTER TABLE public.cases
    ADD CONSTRAINT cases_policy_elapsed_days_nonnegative
    CHECK (policy_elapsed_days IS NULL OR policy_elapsed_days >= 0);

COMMENT ON COLUMN public.cases.policy_elapsed_days IS
'가입 후 경과일. 챗봇에서 약관의 면책·감액 경계에 맞춘 가입기간 구간을 선택받고, 판정용 대표 경과일로 정규화하여 저장한다. 미입력 또는 잘 모르겠어요 선택 시 NULL이며 해당 면책·감액 판정은 확인 불가 처리한다.';

ALTER TABLE public.policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.riders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rider_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diseases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.disease_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.disease_group_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.disease_group_code_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rider_disease_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.treatment_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rider_treatment_rules ENABLE ROW LEVEL SECURITY;

COMMIT;
