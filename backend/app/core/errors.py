"""도메인 예외 + HTTP 상태코드 매핑 (설계서 §4 에러코드 규약)."""


class AppError(Exception):
    """애플리케이션 기본 예외. http_status / code 를 갖는다."""

    http_status = 500
    code = "internal_error"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ValidationError(AppError):       # 400
    http_status = 400
    code = "validation_error"


class AuthError(AppError):             # 401
    http_status = 401
    code = "unauthorized"


class ForbiddenError(AppError):        # 403
    http_status = 403
    code = "forbidden"


class NotFoundError(AppError):         # 404
    http_status = 404
    code = "not_found"


class ParseError(AppError):            # 422
    http_status = 422
    code = "parse_failed"


class LLMUnavailableError(AppError):   # 503
    http_status = 503
    code = "llm_unavailable"
