-- 002_service_domain.sql
-- 서비스 운영 도메인 (소유: 이태경) — cases · analysis_results · reports
-- 사용자는 Supabase Auth(auth.users) 사용 — 자체 users 테이블 없음, user_id 로 참조.
-- DB설계서 v1.6 기준 (coverage_amounts v1.5 · disease 후보 컬럼 v1.6)

-- ============================================================
-- 상황 입력 (분석 1회 = 1행)
-- ============================================================
create table if not exists cases (
    id                       uuid         primary key default gen_random_uuid(),
    user_id                  uuid         not null,                -- auth.users 참조 (Supabase Auth)
    disease_kcd              varchar(10),                         -- KCD 코드 — 예: M51 (추간판장애)
    disease_name             varchar(100) not null,               -- 사용자 입력 질병명
    disease_kcd_candidates   jsonb        not null default '[]',  -- LLM/검색이 찾은 KCD 후보 배열. 예: [{kcd:"M51",confidence:0.86,source:"diseases"}] (v1.6)
    disease_group_candidates jsonb        not null default '[]',  -- 질병군 후보 배열. 예: [{group_id:"disc_disease",confidence:0.82}] (v1.6)
    disease_match_confidence varchar(30),                         -- high / medium / low / need_user_confirmation (v1.6)
    surgery                  boolean      default false,
    diag_days                integer,                             -- 의사 진단 기간 (예: 28)
    current_days             integer,                             -- 현재까지 입원 일수 (예: 14)
    claimed_policy_ids       jsonb        not null default '[]',  -- 이미 청구한 policies.id 배열
    policy_elapsed_days      integer,                             -- 면책·감액 판정용 (보험계약일~현재 일수). null → "확인 불가" 처리
    coverage_amounts         jsonb        not null default '[]',  -- 보장별 가입금액 묶음 [{rider_id,amount,amount_source}]. amount_source: 데모가정(화면 "가입금액 기준 예시" 라벨 강제)/실증권(사용자 증권 입력값). judge() 정액 calc 계산 시 참조. 미입력 보장은 calc=null (v1.5)
    hospitalization_type     varchar(10),                         -- 'INPATIENT' | 'OUTPATIENT'
    additional_treatments    text[]       default '{}',           -- 치료 항목 배열 (체크리스트)
    payment_amount           integer,                             -- 환자 실부담 결제 금액 (원)
    visit_dates              date[]       default '{}',           -- 방문 날짜 배열, 청구 3년 이내 판별용
    annual_visit_count       integer,                             -- 연간 진료 횟수, 특약 한도 판별용
    created_at               timestamptz  not null default now()  -- 마이페이지 이력 정렬 기준
);

-- ============================================================
-- 탐색 결과
-- 스냅샷 규칙: 생성 시점 값 복사 — 이후 riders 변경과 무관하게 불변
-- ============================================================
create table if not exists analysis_results (
    id          uuid         primary key default gen_random_uuid(),
    case_id     uuid         not null references cases(id) on delete cascade, -- cases.id 참조
    rider_id    uuid         not null references riders(id),       -- riders.id 참조 — 디버깅·추적용 (화면 미사용)
    policy_name varchar(200) not null,  -- ★스냅샷: 생성 시점 값 복사 — riders 수정돼도 결과 불변
    rider_name  varchar(200) not null,  -- ★스냅샷
    status      varchar(20)  not null,  -- eligible / claimed / boundary_not_met / not_applicable — judge() 출력
    missed      boolean      default false, -- '놓치고 계실 수 있어요' 표시 여부
    gap_days    integer,                -- 경계까지 부족한 일수 (boundary_not_met일 때)
    evidence    jsonb        not null,  -- ★스냅샷: {"article_no","page","quote(원문)","unit_amount","unit_type","calc"}
    explanation text,                  -- LLM 생성 설명 (원문 컨텍스트 한정)
    created_at  timestamptz  not null default now()
);

-- ============================================================
-- 리포트 (최종 산출물)
-- ============================================================
create table if not exists reports (
    id         uuid        primary key default gen_random_uuid(),
    case_id    uuid        not null references cases(id) on delete cascade, -- cases.id 참조 (1:1)
    user_id    uuid        not null,   -- auth.users 참조 — 본인만 조회 (NFR-11)
    body       jsonb       not null,   -- 상황 요약·청구 가능 보장·비교 결과·체크리스트·소멸시효 안내
    created_at timestamptz not null default now() -- 마이페이지 재열람은 이 시점 스냅샷 기준
);

-- ============================================================
-- 인덱스
-- ============================================================
create index if not exists idx_cases_user
    on cases(user_id);
create index if not exists idx_analysis_results_case
    on analysis_results(case_id);
create index if not exists idx_reports_user
    on reports(user_id);
