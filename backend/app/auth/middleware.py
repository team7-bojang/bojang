from functools import wraps

import jwt  # PyJWT
from flask import g, request
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError

from app.config import settings
from app.core.errors import AuthError

# 디버그 폴백 시 주입할 더미 사용자 ID (로컬 개발 전용).
_DEBUG_USER_ID = "00000000-0000-0000-0000-000000000000"

# Supabase 가 비대칭 키로 서명할 때 쓰는 알고리즘. 이 경우 공유 시크릿이 아니라
# JWKS 공개키로 검증한다. 그 외(HS256)는 레거시 공유 시크릿으로 검증.
_ASYMMETRIC_ALGS = ("ES256", "RS256")

# JWKS 공개키 클라이언트. PyJWKClient 가 키셋을 캐싱하므로 매 요청 네트워크 호출을 피하기
# 위해 모듈 레벨에서 1회만 생성한다.
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def _verify_supabase_jwt(token: str) -> str:
    """Supabase access token 서명·만료·audience 를 검증하고 sub(user_id) 를 반환.

    토큰 헤더의 `alg` 로 검증 경로를 가른다:
    - ES256/RS256 (비대칭) → JWKS 공개키로 검증 (Supabase 신규 서명 키 기본값).
    - HS256 (대칭) → 레거시 공유 시크릿으로 검증.

    검증 실패는 모두 AuthError 로 변환한다. 검증 수단(공개키 URL·시크릿) 미설정은
    설정 오류이므로 프로덕션에서는 검증 불가 상태로 보고 401 을 던진다.
    """
    common_kwargs = {
        "audience": settings.supabase_jwt_audience,
        "options": {"require": ["exp", "sub"]},
    }
    # supabase_url 이 설정돼 있으면 발급자(iss)까지 검증 — 다른 프로젝트가 발급한 토큰 차단.
    if settings.supabase_url:
        common_kwargs["issuer"] = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    try:
        alg = jwt.get_unverified_header(token).get("alg", "")

        if alg in _ASYMMETRIC_ALGS:
            if not settings.supabase_url:
                raise AuthError("Supabase URL 이 설정되지 않아 토큰을 검증할 수 없습니다.")
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(token, signing_key.key, algorithms=list(_ASYMMETRIC_ALGS), **common_kwargs)
        else:
            if not settings.supabase_jwt_secret:
                raise AuthError("JWT Secret 이 설정되지 않아 토큰을 검증할 수 없습니다.")
            payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **common_kwargs)
    except jwt.ExpiredSignatureError:
        raise AuthError("만료된 토큰입니다.") from None
    except (jwt.InvalidTokenError, PyJWKClientError):
        # 서명 불일치·잘못된 audience·형식 오류·공개키 조회 실패 등 검증 실패 전반
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
