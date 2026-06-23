-- 011_policy_pages_page_num_check.sql
-- policy_pages.page_num 1-based 무결성 강제.
-- 조회 로직 전체가 1-based를 전제하므로 DB 레벨 CHECK로 고정한다.
-- 소유: 진미경

ALTER TABLE public.policy_pages
    ADD CONSTRAINT policy_pages_page_num_positive CHECK (page_num >= 1);
