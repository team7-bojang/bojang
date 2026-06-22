-- Migration 003: cases 입원/통원 컬럼 boolean 분리
-- DB설계서 v1.7 반영
-- hospitalization_type(varchar) → is_inpatient(boolean) + is_outpatient(boolean)

BEGIN;

ALTER TABLE cases DROP COLUMN IF EXISTS hospitalization_type;

ALTER TABLE cases ADD COLUMN is_inpatient boolean NOT NULL DEFAULT false;
ALTER TABLE cases ADD COLUMN is_outpatient boolean NOT NULL DEFAULT false;

ALTER TABLE cases ADD CONSTRAINT chk_cases_visit_type
  CHECK (NOT (is_inpatient AND is_outpatient));

COMMIT;
