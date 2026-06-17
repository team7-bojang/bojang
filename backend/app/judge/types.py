"""룰 엔진 입출력 타입 (설계서 6-4-1 인터페이스 계약)."""

from __future__ import annotations

from typing import Any, TypedDict


class Case(TypedDict):
    disease_kcd: str
    surgery: bool
    diag_days: int
    current_days: int
    policy_elapsed_days: int | None  # None → 면책·감액 "확인 불가"


class Rider(TypedDict):
    """riders 테이블 1행 (judge 판정에 쓰는 필드)."""

    trigger_type: str
    boundaries: list[dict[str, Any]]
    exclusions: list[str]
    limits: list[dict[str, Any]]
    waiting_period_days: int | None
    reductions: list[dict[str, Any]]
    deduct_days: int
    unit_amount: int | None
    unit_type: str | None
    claim_rule: dict[str, Any] | None  # None=정액 / not None=실손 정률·공제
    source_pages: list[int]


class Judgement(TypedDict):
    status: str  # core.constants.JudgeStatus
    gap_days: int | None
    matched_boundary: str | None
    calc: str | None
    reduction: dict[str, Any] | None
    limit_note: str | None
