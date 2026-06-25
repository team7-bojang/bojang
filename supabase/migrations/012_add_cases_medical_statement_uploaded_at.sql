-- 012_add_cases_medical_statement_uploaded_at.sql
-- 세부산정내역서 업로드 여부를 visit_dates(결제내역/대시보드 수정에서도 채워지는 공용 필드)와
-- 분리해서 추적하기 위한 컬럼. "1건만 업로드 가능" 가드는 이 컬럼만 기준으로 한다.

ALTER TABLE public.cases
    ADD COLUMN IF NOT EXISTS medical_statement_uploaded_at timestamptz;
