-- 001_policy_domain.sql
-- 약관 도메인 (소유: 진미경) — policies · riders · rider_chunks · diseases · disease_groups
-- ⚠️ 이 도메인 스키마 변경 권한은 진미경 단독. 변경은 새 마이그레이션 파일로만.
-- DB설계서 v1.6 기준 (coverage_kind v1.4 · source_pages v1.3 · 질병군 매핑 레이어 v1.6)

create extension if not exists vector;     -- pgvector
create extension if not exists pg_trgm;    -- diseases 검색용 (GIN trgm 인덱스)

-- ============================================================
-- 보험 상품
-- ============================================================
create table if not exists policies (
    id          uuid        primary key default gen_random_uuid(), -- 보험 상품 고유 ID
    name        text        not null,                              -- 예: ○○ 실손의료비보험
    insurer     text        not null,                              -- 예: A생명, B손해보험
    type        text        check (type in ('실손','암','상해','질병')), -- 실손/암/상해/질병 (CHECK 제약)
    is_preset   boolean     not null default false,                -- true=팀이 사전 구조화한 대표 상품
    pdf_path    text,                                              -- PDF 저장 경로 (Supabase Storage)
    user_id     uuid,                                              -- auth.users 참조 — 업로드 약관일 때만, 선탑재는 NULL
    created_at  timestamptz not null default now()
);

-- ============================================================
-- 보장 단위 (주계약 보장 + 특약) — 프로젝트의 심장
-- ============================================================
create table if not exists riders (
    id                  uuid        primary key default gen_random_uuid(), -- 특약 고유 ID
    policy_id           uuid        not null references policies(id) on delete cascade, -- policies.id 참조
    name                text        not null,           -- 예: 질병입원일당특약
    is_main             boolean     not null default false, -- 주계약(보통약관) 보장이면 true, 특약이면 false
    trigger_type        text,                           -- 입원/수술/진단/통원/내원/골절/치료/사망/후유장해/기타 (검색 1차 필터). 권장값이며 벗어나도 보존+경고
    trigger_detail      text,                           -- 약관의 지급 조건 원문 요약
    unit_amount         integer,                        -- 약관 명시 금액(원) — 예: 50000. 가입금액 기준이면 null
    unit_type           text,                           -- 1일당 / 1회당 / 일시금
    unit_basis          text,                           -- 별표 참조 등 단가 산정 기준 설명
    boundaries          jsonb       default '[]',       -- [{"condition_days":21,"effect":"장기입원 추가 보장"}] — 경계 감지용
    exclusions          jsonb       default '[]',       -- 질적 제외 조건만 — 예: ["치아파절 제외","요양병원 제외"] (일수 공제→deduct_days, 대기기간→waiting_period_days)
    limits              jsonb       default '[]',       -- [{"scope":"per_hospitalization","unit":"days","value":180}] — scope: per_hospitalization/annual/daily/same_cause_window
    waiting_period_days integer,                        -- 계약일로부터 N일 보장제외 (예: 암 90일). null=없음. judge에서 policy_elapsed_days와 비교
    reductions          jsonb       default '[]',       -- [{"until_elapsed_days":730,"rate":0.5}] — 가입 후 N일 이내 지급사유 발생 시 비율 지급 (한화 2년 50%)
    deduct_days         integer     default 0,          -- 지급 시작 offset — 예: DB 뇌혈관 3 (4일째부터 지급). calc: 단가×(입원일수−deduct_days)
    article_no          text,                           -- 예: 제15조 ②항
    page                integer,                        -- 약관 PDF 페이지 번호
    raw_text            text,                           -- 조항 원문 전문 — LLM 인용 검증(문자열 대조)에 사용
    source_pages        jsonb       default '[]',       -- 여러 페이지로 쪼개진 보장을 병합한 경우 출처 페이지 배열 — 예: [37,38]. 단일 페이지 보장은 빈 배열 또는 [page]. 근거 추적용 (v1.3)
    verified            boolean     not null default false, -- 수동 검수 통과 시 true. false도 탐색·임베딩 포함, 화면에 "관련 가능 보장" 배지 + 정밀 판정 미표시
    coverage_kind       varchar(10) not null default '정액' check (coverage_kind in ('정액','실손')), -- 정액/실손 (CHECK 제약). 지급방식 구분의 단일 출처(single source of truth) — 프론트 카드 분기·검색 필터·judge 분기가 이 컬럼만 참조. v1.4
    claim_rule          jsonb,                          -- 실손=정률·공제 규칙 {cause_type,medical_category,visit_type,reimbursement_rate,deductible,formula}. 정액=null. 이중차감 금지. v1.4: coverage_kind 분리
    created_at          timestamptz not null default now()
);

-- ============================================================
-- 검색 인덱스 (청킹·임베딩)
-- ============================================================
create table if not exists rider_chunks (
    id        uuid          primary key default gen_random_uuid(),
    rider_id  uuid          not null references riders(id) on delete cascade, -- riders.id 참조
    content   text          not null,       -- 특약 단위 청킹 (특약 1개 = 청크 1~3개)
    embedding vector(1536),                 -- pgvector — ivfflat 인덱스 (vector_cosine_ops)
    meta      jsonb         default '{}'    -- {"policy_id","page","article_no","trigger_type"} — 검색 필터용
);

-- ============================================================
-- 질병코드 마스터 (KCD 후보 검색)
-- ============================================================
create table if not exists diseases (
    kcd         varchar(10)  primary key,   -- KCD 코드. 예: M51
    name        varchar(200) not null,      -- 표준 질병명. 예: 기타 추간판장애
    search_text text         not null       -- 대표명+별칭. 자동완성/LIKE/trgm 검색용
);

-- ============================================================
-- 질병군 마스터 — 약관 표현과 KCD 사이의 중간 분류 (v1.6)
-- ============================================================
create table if not exists disease_groups (
    id                       text    primary key,  -- 예: general_cancer_excl_similar, disc_disease
    name                     text    not null,     -- 예: 일반암(유사암 제외), 디스크질환
    group_type               text    not null check (group_type in ('disease','injury','cancer','treatment_context','non_kcd')), -- disease/injury/cancer/treatment_context/non_kcd
    match_priority           int     not null default 50,  -- 후보가 여러 개일 때 정렬 가중치
    requires_policy_appendix boolean not null default false, -- 보험사별 분류표 확인이 필요한 질병군이면 true
    description              text,                -- 관리자/개발자용 설명
    user_label               text    not null     -- 화면에 보여줄 쉬운 표현. 예: 디스크 관련 질환
);

-- 질병군 별칭 (사용자 표현/약관 표현 매핑)
create table if not exists disease_group_aliases (
    id       bigserial primary key,               -- 별칭 고유 ID
    group_id text      not null references disease_groups(id) on delete cascade, -- disease_groups.id 참조
    alias    text      not null,                  -- 예: 허리디스크, 목디스크, 유사암
    source   text      not null default 'service', -- service / policy / user 등
    unique (group_id, alias)                      -- 질병군별 별칭 중복 방지
);

-- 질병군 KCD 포함/제외 범위
create table if not exists disease_group_code_rules (
    id          bigserial primary key,            -- 코드 규칙 고유 ID
    group_id    text      not null references disease_groups(id) on delete cascade, -- disease_groups.id 참조
    rule_type   text      not null check (rule_type in ('include','exclude')), -- include / exclude
    code_start  text      not null,               -- 예: C00, C73, M51
    code_end    text,                             -- 범위형일 때만 사용. 예: C97
    code_system text      not null default 'KCD', -- KCD 기준
    confidence  text      not null default 'policy_review_required' check (confidence in ('high','medium','policy_review_required')), -- high/medium/policy_review_required
    note        text                              -- 약관 별표 검수 필요 사항
);

-- 특약-질병군 매칭 규칙 (소유: 진미경/이태경 공동)
create table if not exists rider_disease_rules (
    id                   bigserial primary key,   -- 매칭 규칙 고유 ID
    policy_id            uuid references policies(id) on delete cascade, -- policies.id 참조. 공통 패턴 규칙이면 null 가능
    rider_id             uuid references riders(id) on delete cascade,   -- riders.id 참조. 적재 후 고정 매핑 권장
    rider_name_pattern   text,                    -- 초기 MVP용 LIKE 패턴. 예: %유사암진단%
    rule_type            text not null check (rule_type in ('required','excluded','optional')), -- required/excluded/optional
    group_id             text not null references disease_groups(id), -- disease_groups.id 참조
    require_trigger_type text,                    -- 진단/수술/입원/통원 등 추가 조건
    note                 text,                    -- 예: 실손은 optional, 암진단비는 required
    unique (policy_id, rider_id, rider_name_pattern, rule_type, group_id) -- 중복 규칙 적재 방지
);

-- ============================================================
-- 인덱스
-- ============================================================
create index if not exists idx_riders_policy
    on riders(policy_id);
create index if not exists idx_rider_chunks_embedding
    on rider_chunks using ivfflat (embedding vector_cosine_ops);
create index if not exists idx_diseases_search
    on diseases using gin (search_text gin_trgm_ops);
create index if not exists idx_disease_group_aliases_alias
    on disease_group_aliases(alias);
create index if not exists idx_disease_group_code_rules_group
    on disease_group_code_rules(group_id);
create index if not exists idx_rider_disease_rules_rider
    on rider_disease_rules(rider_id, group_id);
