-- 014_add_cases_medical_statement_amounts.sql
-- 진료비 세부산정내역서에서 추출한 항목별 금액과 본인부담금/공단부담금/전액본인부담/비급여
-- 분리값을 영구 저장한다. 기존에는 save_medical_detail_statement 응답 1회성으로만 노출되고
-- DB에 남지 않아, 분석(/api/v1/analysis/search) 시점에 judge 엔진이 payment_amount 합계 외에는
-- 참조할 수 없었다. 약관 기반 예상 보험금 계산에 항목별/구분별 금액이 필요해 컬럼으로 영구화한다.

ALTER TABLE public.cases
    ADD COLUMN IF NOT EXISTS medical_statement_items jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS total_amount integer,
    ADD COLUMN IF NOT EXISTS patient_paid_amount integer,
    ADD COLUMN IF NOT EXISTS nhis_paid_amount integer,
    ADD COLUMN IF NOT EXISTS full_self_pay_amount integer,
    ADD COLUMN IF NOT EXISTS non_covered_amount integer;

COMMENT ON COLUMN public.cases.medical_statement_items IS
    '진료비 세부산정내역서 항목별 금액 배열 [{name,amount,is_non_covered,count}, ...]. summary 검증 실패 시에도 items는 저장됨.';
COMMENT ON COLUMN public.cases.total_amount IS '세부산정내역서 합계 행 총액. summary 산식 검증 실패 시 null.';
COMMENT ON COLUMN public.cases.patient_paid_amount IS '세부산정내역서 합계 행 본인부담금(일부본인부담). summary 산식 검증 실패 시 null.';
COMMENT ON COLUMN public.cases.nhis_paid_amount IS '세부산정내역서 합계 행 공단부담금. summary 산식 검증 실패 시 null.';
COMMENT ON COLUMN public.cases.full_self_pay_amount IS '세부산정내역서 합계 행 전액본인부담. summary 산식 검증 실패 시 null.';
COMMENT ON COLUMN public.cases.non_covered_amount IS '세부산정내역서 합계 행 비급여. summary 산식 검증 실패 시 null.';
