"""공통 응답 봉투·에러 모델 (Swagger 표시용)."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str


class Envelope(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None
    timestamp: str  # ISO 8601
    request_id: str  # uuid 8자리
