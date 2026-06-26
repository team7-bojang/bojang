"""보험 상품(policy) 스키마 (SCR-01/02)."""

from pydantic import BaseModel

from app.schemas.rider import Rider


class PolicyPreset(BaseModel):
    id: str
    name: str
    insurer: str
    type: str  # 실손/암/상해/질병

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "3f2a1b5c-1111-2222-3333-444455556666",
                "name": "무배당 건강보험",
                "insurer": "삼성생명",
                "type": "질병",
            }
        }
    }


class PolicyWithRiders(BaseModel):
    policy: PolicyPreset
    riders: list[Rider]

    model_config = {
        "json_schema_extra": {
            "example": {
                "policy": {
                    "id": "3f2a1b5c-1111-2222-3333-444455556666",
                    "name": "무배당 건강보험",
                    "insurer": "삼성생명",
                    "type": "질병",
                },
                "riders": [
                    {
                        "id": "8b7c0d1e-aaaa-bbbb-cccc-ddddeeeeffff",
                        "name": "뇌혈관질환 진단비 특약",
                        "is_main": False,
                        "trigger_type": "diagnosis",
                        "unit_amount": 20000000,
                        "unit_type": "fixed",
                        "waiting_period_days": 90,
                        "claim_rule": None,
                        "source_pages": [12, 13],
                        "verified": True,
                    }
                ],
            }
        }
    }
