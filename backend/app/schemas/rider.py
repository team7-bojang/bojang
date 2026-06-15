"""riders(보장 단위) 스키마 — claim_rule·source_pages 포함 (v1.3).

⚠️ riders 구조화 스키마 변경 권한은 진미경 단독. 임의 변경 금지.
"""

from typing import Any

from pydantic import BaseModel


class Rider(BaseModel):
    id: str
    name: str
    is_main: bool
    trigger_type: str
    trigger_detail: str | None = None
    unit_amount: int | None = None
    unit_type: str | None = None
    unit_basis: str | None = None
    boundaries: list[dict[str, Any]] = []
    exclusions: list[str] = []
    limits: list[dict[str, Any]] = []
    waiting_period_days: int | None = None
    reductions: list[dict[str, Any]] = []
    deduct_days: int = 0
    claim_rule: dict[str, Any] | None = None  # 정액=null, 실손=정률·공제 규칙
    source_pages: list[int] = []
    article_no: str | None = None
    page: int | None = None
    verified: bool = False
