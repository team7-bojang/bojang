"""헬스 체크 응답."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
