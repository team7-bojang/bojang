"""보험 상품(policy) 스키마 (SCR-01/02)."""

from pydantic import BaseModel

from app.schemas.rider import Rider


class PolicyPreset(BaseModel):
    id: str
    name: str
    insurer: str
    type: str  # 실손/암/상해/질병


class PolicyWithRiders(BaseModel):
    policy: PolicyPreset
    riders: list[Rider]
