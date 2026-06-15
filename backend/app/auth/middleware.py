"""JWT 검증 데코레이터.

@require_auth: Authorization: Bearer <jwt> 서명·만료 검증 → user_id 추출 →
요청 컨텍스트(g.user_id) 주입. 실패 시 401 (core.errors.AuthError).
"""

# TODO: require_auth 데코레이터 구현 (Supabase JWKS 검증)
