-- 015_drop_cases_medical_statement_amounts.sql
-- total_amount/nhis_paid_amount/full_self_pay_amount 는 더 이상 DB에 영구 저장하지 않고,
-- save_medical_detail_statement 응답(extracted_medical_info)에서 코드로 추출해 1회성으로만 노출한다.

ALTER TABLE public.cases
    DROP COLUMN IF EXISTS total_amount,
    DROP COLUMN IF EXISTS nhis_paid_amount,
    DROP COLUMN IF EXISTS full_self_pay_amount;
