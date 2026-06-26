"""공통 응답 봉투·에러 모델 (Swagger 표시용)."""

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str

    model_config = {
        "json_schema_extra": {"example": {"code": "not_found", "message": "해당 리소스를 찾을 수 없습니다."}}
    }


class Envelope[T](BaseModel):
    """성공 응답 봉투 (Swagger 표시용). `ok()` 출력 구조와 일치한다.

    data 를 필수(Optional 아님)로 둬야 Swagger 예시에 실제 응답 객체가 채워진다.
    (제네릭이라 봉투 자체에는 고정 example 을 둘 수 없고, data 의 example 은 각 응답 모델이 제공한다.)
    실패 응답은 별도의 ErrorResponse 로 문서화한다.
    """

    success: bool = True
    data: T
    timestamp: str  # ISO 8601
    request_id: str  # uuid 8자리


class ErrorResponse(BaseModel):
    """실패 응답 봉투 (Swagger 에러 응답 문서화용). `fail()` 출력 구조와 일치한다."""

    success: bool = False
    error: ErrorBody
    timestamp: str  # ISO 8601
    request_id: str  # uuid 8자리

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": {"code": "not_found", "message": "해당 리소스를 찾을 수 없습니다."},
                "timestamp": "2026-06-26T08:30:00.123456+00:00",
                "request_id": "a1b2c3d4",
            }
        }
    }
