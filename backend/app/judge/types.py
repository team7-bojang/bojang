"""룰 엔진 입출력 타입 (설계서 6-4-1 인터페이스 계약).

Judgement 는 특약 1건의 판정 결과 + 금액 4종 + 사유를 담는다.
analysis_results 의 하늘색 컬럼(가입금액/예상보험금/감액금액/추가보험금액)이 여기서 나온다.
총예상보험금은 여러 건의 expected_amount 합 → judge 밖(서비스)에서 집계한다.
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class Case(TypedDict):
    disease_kcd: str
    disease_name: NotRequired[str]
    surgery: bool
    diag_days: int
    current_days: int
    policy_elapsed_days: int | None  # None → 면책·감액 "확인 불가"
    coverage_amounts: NotRequired[Any]  # 보장별 가입금액 [{rider_id, amount, amount_source}]
    payment_amount: NotRequired[int | None]  # 결제금액 = 실손 covered_amount
    claimed: NotRequired[list[Any]]  # 기청구 보험(보험명/ID) 목록
    is_deceased: NotRequired[bool]
    covered_amounts: NotRequired[Any]  # 실손 보상대상 의료비(특약별) [{rider_id/key, amount}]
    # ── resolver(룰테이블)가 채워주는 정밀 매칭 입력 (없으면 judge가 키워드 폴백) ──
    disease_groups: NotRequired[list[str]]  # 이 질병이 속한 질병군 id 목록
    treatment_codes: NotRequired[list[str]]  # 표준화된 치료항목 코드 목록


class Rider(TypedDict):
    """riders 테이블 1행 (judge 판정에 쓰는 필드)."""

    name: NotRequired[str]
    id: NotRequired[str]
    policy_id: NotRequired[str]
    coverage_kind: NotRequired[str]  # '정액' | '실손' (지급방식 단일 출처)
    trigger_type: str
    trigger_detail: NotRequired[str]
    boundaries: list[dict[str, Any]]
    exclusions: list[str]
    limits: list[dict[str, Any]]
    waiting_period_days: int | None
    reductions: list[dict[str, Any]]
    deduct_days: int
    unit_amount: int | None
    unit_type: str | None
    unit_basis: NotRequired[str | None]
    claim_rule: dict[str, Any] | None  # None=정액 / not None=실손 정률·공제
    source_pages: list[int]
    # ── resolver(룰테이블)가 채워주는 매칭 규칙 (없으면 judge가 키워드 폴백) ──
    require_groups: NotRequired[list[str]]  # 요구 질병군 (rider_disease_rules)
    exclude_groups: NotRequired[list[str]]  # 제외 질병군
    require_treatments: NotRequired[list[str]]  # 요구 치료항목 코드 (rider_treatment_rules)


class Judgement(TypedDict):
    status: str  # core.constants.JudgeStatus
    gap_days: int | None
    matched_boundary: str | None
    calc: str | None
    reduction: dict[str, Any] | None
    limit_note: str | None
    # ── 금액(하늘색) ──
    subscribed_amount: int | None  # 가입금액 (입력에서 받은 값)
    expected_amount: int | None  # 예상보험금 (이 특약 1건, 감액 반영 후)
    reduced_amount: int | None  # 감액금액 (감액으로 못 받는 금액) → CASE 2-2
    additional_amount: int | None  # 추가보험금액 (조건 충족 시 더 받을 금액) → CASE 2-1
    reason: str | None  # 미달·감액 사유 ("입원 3일 이상 필요" 등)


_DEFAULT_JUDGEMENT: Judgement = {
    "status": "",
    "gap_days": None,
    "matched_boundary": None,
    "calc": None,
    "reduction": None,
    "limit_note": None,
    "subscribed_amount": None,
    "expected_amount": None,
    "reduced_amount": None,
    "additional_amount": None,
    "reason": None,
}


def new_judgement(status: str, **over: Any) -> Judgement:
    """모든 키가 채워진 Judgement 를 만든다 (계약 일관성 보장)."""
    out: Judgement = dict(_DEFAULT_JUDGEMENT)  # type: ignore[assignment]
    out["status"] = status
    out.update(over)  # type: ignore[typeddict-item]
    return out
