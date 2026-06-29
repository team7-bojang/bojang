-- 016_policies_pdf_hash.sql
-- 사용자 업로드 약관 PDF 재업로드 시 동일 파일을 식별해 텍스트 추출/온디맨드 파싱을 재사용하기 위한 컬럼.
-- 같은 사용자가 동일 PDF(sha256 동일)를 다시 업로드하면 기존 policy_id 를 그대로 반환한다.
-- 소유: 진미경

ALTER TABLE public.policies
    ADD COLUMN IF NOT EXISTS pdf_hash text;

COMMENT ON COLUMN public.policies.pdf_hash IS
    '업로드 PDF 원본 바이트의 sha256 해시. 사용자 업로드 약관만 채워짐(preset 은 NULL).';

-- 조회 패턴: 동일 사용자의 동일 PDF 재업로드 감지 (user_policy_service.upload_pdf)
CREATE INDEX IF NOT EXISTS policies_user_id_pdf_hash_idx
    ON public.policies (user_id, pdf_hash)
    WHERE pdf_hash IS NOT NULL;
