"""DB 접근 계층 (Supabase / pgvector).

도메인 소유: policies·riders·rider_chunks=진미경 / cases·analysis_results·reports=이태경.
스키마 변경은 supabase/migrations/NNN_설명.sql 단일 채널 + 소유자 승인.
"""

from app.db.client import get_client

__all__ = ["get_client"]
