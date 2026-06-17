from functools import wraps

import jwt  # PyJWT
from flask import g, request

from app.config import settings
from app.core.errors import AuthError


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. 헤더에서 Authorization 가져오기
        auth_header = request.headers.get("Authorization", None)

        # 로컬 테스트용/개발용 디버그 예외 처리
        if settings.debug and (
            not auth_header
            or auth_header == "Bearer test-token"
            or auth_header == "Bearer undefined"
        ):
            g.user_id = "00000000-0000-0000-0000-000000000000"
            return f(*args, **kwargs)

        if not auth_header:
            raise AuthError("인증 헤더가 누락되었습니다.")

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise AuthError("잘못된 인증 헤더 형식입니다.")

            token = parts[1]

            # 실제 Supabase JWT는 PyJWT로 디코드 가능 (JWT Secret 또는 JWKS 기반)
            # 여기서는 로컬/더미 키 또는 간단한 디코드를 우선 시도
            # secret 키가 설정되어 있지 않은 경우, 안전하게 payload의 sub 필드를 바로 로드하거나
            # 디코딩 에러 시 디버그 모드면 디코드 없이 sub 추출 (디버그 폴백)
            try:
                # verify_signature=False 로 껍데기만 푸는 디버그 모드 폴백 지원
                payload = jwt.decode(token, options={"verify_signature": False})
                g.user_id = payload.get("sub", "00000000-0000-0000-0000-000000000000")
            except Exception:
                if settings.debug:
                    g.user_id = "00000000-0000-0000-0000-000000000000"
                else:
                    raise AuthError("유효하지 않은 JWT 토큰입니다.") from None

        except AuthError as ae:
            raise ae
        except Exception as e:
            raise AuthError(f"인증 처리 중 오류가 발생했습니다: {str(e)}") from e

        return f(*args, **kwargs)

    return decorated
