-- 002_service_domain.sql
-- 서비스 운영 도메인 (소유: 이태경) — cases · analysis_results · reports
-- 사용자는 Supabase Auth(auth.users) 사용 — 자체 users 테이블 없음, user_id 로 참조.

-- 상황 입력
create table if not exists cases (
    id                  uuid primary key default gen_random_uuid(),
    user_id             uuid not null,   -- auth.users 참조
    disease_kcd         text,
    disease_name        text,
    surgery             boolean default false,
    diag_days           integer,
    current_days        integer,
    claimed_policy_ids  jsonb default '[]',
    policy_elapsed_days integer,         -- null → 면책·감액 "확인 불가"
    created_at          timestamptz not null default now()
);

-- 탐색 결과 (스냅샷 규칙: 생성 시점 값 복사, 이후 riders 변경과 무관하게 불변)
create table if not exists analysis_results (
    id          uuid primary key default gen_random_uuid(),
    case_id     uuid not null references cases(id) on delete cascade,
    rider_id    uuid,                    -- 추적용 참조 (화면 미사용)
    policy_name text,                    -- 스냅샷
    rider_name  text,                    -- 스냅샷
    status      text,                    -- judge() 출력
    missed      boolean default false,
    gap_days    integer,
    evidence    jsonb,                   -- 스냅샷 {article_no, page, quote, unit_amount, ...}
    explanation text,
    created_at  timestamptz not null default now()
);

-- 리포트
create table if not exists reports (
    id         uuid primary key default gen_random_uuid(),
    case_id    uuid not null references cases(id) on delete cascade,
    user_id    uuid not null,
    body       jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_cases_user on cases(user_id);
create index if not exists idx_analysis_results_case on analysis_results(case_id);
