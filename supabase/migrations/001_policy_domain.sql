-- 001_policy_domain.sql
-- 약관 도메인 (소유: 진미경) — policies · riders · rider_chunks
-- ⚠️ 이 도메인 스키마 변경 권한은 진미경 단독. 변경은 새 마이그레이션 파일로만.

create extension if not exists vector;  -- pgvector

-- 보험 상품
create table if not exists policies (
    id        uuid primary key default gen_random_uuid(),
    name      text not null,
    insurer   text not null,
    type      text,                 -- 실손/암/상해/질병
    is_preset boolean not null default false,
    pdf_path  text
);

-- 보장 단위 (주계약 보장 + 특약) — 프로젝트의 심장
create table if not exists riders (
    id                  uuid primary key default gen_random_uuid(),
    policy_id           uuid not null references policies(id) on delete cascade,
    name                text not null,
    is_main             boolean not null default false,
    trigger_type        text,
    trigger_detail      text,
    unit_amount         integer,
    unit_type           text,
    unit_basis          text,
    boundaries          jsonb default '[]',
    exclusions          jsonb default '[]',
    limits              jsonb default '[]',
    waiting_period_days integer,
    reductions          jsonb default '[]',
    deduct_days         integer default 0,
    claim_rule          jsonb,             -- 정액=null, 실손=정률·공제 규칙 (v1.3)
    source_pages        jsonb default '[]',-- 병합 보장 출처 페이지 (v1.3)
    article_no          text,
    page                integer,
    raw_text            text,              -- 인용 검증용 원문
    verified            boolean not null default false
);

-- 검색 인덱스 (청킹·임베딩)
create table if not exists rider_chunks (
    id        uuid primary key default gen_random_uuid(),
    rider_id  uuid not null references riders(id) on delete cascade,
    content   text not null,
    embedding vector(1536),
    meta      jsonb default '{}'  -- {policy_id, page, article_no, trigger_type}
);

create index if not exists idx_riders_policy on riders(policy_id);
create index if not exists idx_rider_chunks_embedding
    on rider_chunks using ivfflat (embedding vector_cosine_ops);
