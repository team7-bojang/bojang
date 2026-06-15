"""공통 응답 봉투·에러 모델 (Swagger 표시용)."""

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str


class Envelope[T](BaseModel):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None
    timestamp: str  # ISO 8601
    request_id: str  # uuid 8자리
