-- Migration 004: cases 컬럼명을 API/DB 설계서 v1.9 기준으로 변경
-- 선행 migration: 002_service_domain.sql, 003_cases_visit_type_boolean.sql

BEGIN;

ALTER TABLE public.cases
    RENAME COLUMN diag_days TO admission_days_diagnosed;

ALTER TABLE public.cases
    RENAME COLUMN current_days TO admission_days_current;

ALTER TABLE public.cases
    RENAME COLUMN additional_treatments TO treatment_items;

COMMIT;
