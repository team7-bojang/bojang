from functools import wraps

import jwt  # PyJWT
from flask import g, request

from app.config import settings
from app.core.errors import AuthError

# 디버그 폴백 시 주입할 더미 사용자 ID (로컬 개발 전용).
_DEBUG_USER_ID = "00000000-0000-0000-0000-000000000000"


def _verify_supabase_jwt(token: str) -> str:
    """Supabase access token(HS256) 서명·만료·audience 를 검증하고 sub(user_id) 를 반환.

    검증 실패는 모두 AuthError 로 변환한다. JWT Secret 미설정은 설정 오류이므로
    프로덕션에서는 검증 불가 상태로 보고 401 을 던진다.
    """
    if not settings.supabase_jwt_secret:
        raise AuthError("JWT Secret 이 설정되지 않아 토큰을 검증할 수 없습니다.")

    decode_kwargs = {
        "algorithms": ["HS256"],
        "audience": settings.supabase_jwt_audience,
        "options": {"require": ["exp", "sub"]},
    }
    # supabase_url 이 설정돼 있으면 발급자(iss)까지 검증 — 다른 프로젝트가 발급한 토큰 차단.
    if settings.supabase_url:
        decode_kwargs["issuer"] = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, **decode_kwargs)
    except jwt.ExpiredSignatureError:
        raise AuthError("만료된 토큰입니다.") from None
    except jwt.InvalidTokenError:
        # 서명 불일치·잘못된 audience·형식 오류 등 PyJWT 검증 실패 전반
        raise AuthError("유효하지 않은 JWT 토큰입니다.") from None

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("토큰에 사용자 식별자(sub)가 없습니다.")
    return user_id


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)

        # 로컬 개발용 디버그 폴백: 헤더가 없거나 더미 토큰이면 검증을 건너뛴다.
        # 프로덕션(debug=False)에서는 절대 타지 않는다.
        if settings.debug and (not auth_header or auth_header in ("Bearer test-token", "Bearer undefined")):
            g.user_id = _DEBUG_USER_ID
            return f(*args, **kwargs)

        if not auth_header:
            raise AuthError("인증 헤더가 누락되었습니다.")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthError("잘못된 인증 헤더 형식입니다.")

        g.user_id = _verify_supabase_jwt(parts[1])
        return f(*args, **kwargs)

    return decorated
