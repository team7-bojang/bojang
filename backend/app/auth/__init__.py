"""인증 (F-05, 진미경) — Supabase JWT 검증 미들웨어.

백엔드는 자체 인증 로직 없이 요청 헤더의 Supabase JWT 만 검증한다.
가입/로그인은 프론트가 Supabase Auth SDK 로 직접 처리.
"""
from app.auth.middleware import require_auth

__all__ = ["require_auth"]
