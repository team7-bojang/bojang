-- Migration 005: 치료항목 마스터 및 특약-치료항목 매핑 테이블
-- 선행 migration: 001_policy_domain.sql ~ 004_alter_cases_columns.sql
-- 주의: rider별 실제 매핑 데이터는 riders 적재 후 seed_treatment_rules.sql로 등록한다.

BEGIN;

CREATE TABLE IF NOT EXISTS public.treatment_types (
    code         varchar(30)  PRIMARY KEY,
    ui_group     varchar(50)  NOT NULL,
    display_name varchar(100) NOT NULL,
    aliases      text[]       NOT NULL DEFAULT '{}',
    active       boolean      NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS public.rider_treatment_rules (
    id             bigserial   PRIMARY KEY,
    rider_id       uuid        NOT NULL
        REFERENCES public.riders(id) ON DELETE CASCADE,
    treatment_code varchar(30) NOT NULL
        REFERENCES public.treatment_types(code),
    rule_type      varchar(20) NOT NULL
        CHECK (rule_type IN ('required', 'excluded', 'optional')),
    note           text,

    CONSTRAINT uq_rider_treatment_rule
        UNIQUE (rider_id, treatment_code, rule_type)
);

INSERT INTO public.treatment_types (
    code,
    ui_group,
    display_name,
    aliases,
    active
)
VALUES
    (
        'MRI_MRA',
        '영상검사',
        'MRI/MRA',
        ARRAY['MRI', 'MRA', '자기공명영상', 'MRI 촬영', '자기공명영상진단'],
        true
    ),
    (
        'CT',
        '영상검사',
        'CT 검사',
        ARRAY['CT', 'CT촬영', '전산화단층촬영'],
        true
    ),
    (
        'XRAY',
        '영상검사',
        '엑스레이',
        ARRAY['X-ray', '엑스레이', '방사선 촬영', '단순방사선'],
        true
    ),
    (
        'MANUAL_THERAPY',
        '도수·충격파',
        '도수치료',
        ARRAY['도수치료', '도수', '수기치료'],
        true
    ),
    (
        'PHYSICAL_THERAPY',
        '물리치료',
        '일반 물리치료',
        ARRAY['물리치료', '물리요법'],
        true
    ),
    (
        'ECSWT',
        '도수·충격파',
        '체외충격파',
        ARRAY['체외충격파', 'ECSWT', '충격파치료'],
        true
    ),
    (
        'INJECTION',
        '주사치료',
        '주사치료',
        ARRAY['주사', '주사치료', '주사료', '비급여주사'],
        true
    ),
    (
        'MEDICATION',
        '기타',
        '약 처방',
        ARRAY['약 처방', '투약', '약제비', '처방약'],
        true
    ),
    (
        'CAST',
        '기타',
        '깁스',
        ARRAY['깁스', '석고붕대', '통깁스'],
        true
    ),
    (
        'BRACE_SPLINT',
        '기타',
        '보조기·부목',
        ARRAY['보조기', '부목', '스플린트'],
        true
    ),
    (
        'EMERGENCY',
        '기타',
        '응급실 진료',
        ARRAY['응급실', '응급', '응급진료', '응급내원'],
        true
    ),
    (
        'OTHER',
        '기타',
        '기타 치료',
        ARRAY['기타'],
        true
    )
ON CONFLICT (code) DO UPDATE
SET
    ui_group = EXCLUDED.ui_group,
    display_name = EXCLUDED.display_name,
    aliases = EXCLUDED.aliases,
    active = EXCLUDED.active;

ALTER TABLE public.treatment_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rider_treatment_rules ENABLE ROW LEVEL SECURITY;

COMMIT;
