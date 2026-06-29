"""탐색·비교(F-02/F-03) 응답 스키마."""

from pydantic import BaseModel


class Evidence(BaseModel):
    article: str | None = None
    page: int | None = None
    quote: str | None = None


class CoverageResult(BaseModel):
    policy: str
    rider: str
    status: str  # judge 출력 (eligible/claimed/boundary_not_met/.../potential)
    coverage_kind: str | None = None  # 정액/실손
    is_daily: bool = False  # True=입원일당(특별약관 가입금액=1일당), False=진단/정액(가입금액)
    missed: bool = False
    gap_days: int | None = None
    estimated_amount: int = 0  # 현재 받을 수 있는 (감액 반영 후)
    additional_amount: int = 0  # 조건 충족 시 추가로 받을 수 있는
    reduced_amount: int = 0  # 감액으로 못 받는 금액
    calc: str | None = None
    explanation: str | None = None
    evidence: Evidence | None = None


class SearchSummary(BaseModel):
    eligible_count: int
    missed_count: int


class Case2SummaryItem(BaseModel):
    rider: str | None = None
    policy: str | None = None
    amount: int = 0
    condition: str | None = None
    reason: str | None = None


class Case2Summary(BaseModel):
    """CASE2 추가 보장·감액 막대그래프 집계."""

    current_total: int = 0
    additional_total: int = 0
    potential_total: int = 0
    reduced_total: int = 0
    before_reduction_total: int = 0
    additional_items: list[Case2SummaryItem] = []
    reduced_items: list[Case2SummaryItem] = []


class SearchResponse(BaseModel):
    summary: SearchSummary
    results: list[CoverageResult]
    case2_summary: Case2Summary | None = None
    notice: str | None = None


class CoverageAmountInput(BaseModel):
    """보장별 가입금액 (judge 정액 금액 산출용). DB 저장 없이 판정 시점에만 사용."""

    rider_id: str
    amount: int
    amount_source: str | None = None


class SearchRequest(BaseModel):
    case_id: str
    # 가입금액 입력 후 재판정 시, DB 저장 없이 이 값으로 예상 보험금을 재계산한다.
    # (None 이면 기존 case 의 coverage_amounts 를 사용)
    coverage_amounts: list[CoverageAmountInput] | None = None
    # 실손 covered_amount 직접 입력 (judge 재계산 전용, DB 미저장).
    # 급여 실손 → patient_paid_amount, 비급여 실손 → non_covered_amount.
    # (None 이면 기존 case 저장값을 사용, 둘 다 없으면 실손은 보류)
    patient_paid_amount: int | None = None
    non_covered_amount: int | None = None


# ── POST /analysis/compare (API 15) v2.1 ──
class ScenarioInput(BaseModel):
    days: int
    name: str


class CompareRequest(BaseModel):
    case_id: str
    # v2.1 다중 시나리오 입력. 옛 형식(current_days/target_days)도 호환한다.
    scenarios: list[ScenarioInput] | None = None
    current_days: int | None = None
    target_days: int | None = None


class ScenarioOutput(BaseModel):
    name: str


class Outcome(BaseModel):
    status: str
    calc: str | None = None
    gap_days: int | None = None


class Comparison(BaseModel):
    policy: str
    rider: str
    outcomes: list[Outcome]


class CompareResponse(BaseModel):
    scenarios: list[ScenarioOutput]
    comparisons: list[Comparison]
