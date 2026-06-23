-- 008_policy_pages.sql
-- 사용자 업로드 PDF의 페이지별 텍스트를 저장하는 테이블.
-- 온디맨드 파싱 흐름에서 키워드 기반 관련 페이지 필터링에 사용한다.
-- 소유: 진미경

-- pg_trgm: 한국어 포함 트리그램 전문 검색 인덱스에 필요
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS public.policy_pages (
    id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    policy_id   uuid        NOT NULL REFERENCES public.policies(id) ON DELETE CASCADE,
    page_num    integer     NOT NULL,
    text        text        NOT NULL,
    created_at  timestamptz DEFAULT now(),
    -- 같은 policy의 같은 페이지 번호 중복 방지 (재업로드 시 upsert 충돌 감지)
    UNIQUE (policy_id, page_num)
);

-- 조회 패턴: policy_id로 전체 페이지 가져오기 + page_num 정렬
CREATE INDEX IF NOT EXISTS policy_pages_policy_id_page_num_idx
    ON public.policy_pages (policy_id, page_num);

-- 전문 검색용 트리그램 인덱스 (pg_trgm 필수)
CREATE INDEX IF NOT EXISTS policy_pages_text_trgm_idx
    ON public.policy_pages USING gin (text gin_trgm_ops);

-- RLS: 본인 policy 의 페이지만 접근 가능
ALTER TABLE public.policy_pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "policy_pages_owner_select"
    ON public.policy_pages FOR SELECT
    USING (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "policy_pages_owner_insert"
    ON public.policy_pages FOR INSERT
    WITH CHECK (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "policy_pages_owner_delete"
    ON public.policy_pages FOR DELETE
    USING (
        policy_id IN (
            SELECT id FROM public.policies WHERE user_id = auth.uid()
        )
    );

COMMENT ON TABLE public.policy_pages IS
    '사용자 업로드 약관 PDF의 페이지별 원문 텍스트. 온디맨드 파싱 시 키워드 필터에 사용.';
COMMENT ON COLUMN public.policy_pages.policy_id IS 'policies.id 참조. is_preset=false 인 사용자 업로드 약관만 대상.';
COMMENT ON COLUMN public.policy_pages.page_num IS 'PDF 1-based 페이지 번호.';
COMMENT ON COLUMN public.policy_pages.text IS 'pdfplumber 추출 원문. 표 포함 [TABLE] 마커 형식.';
