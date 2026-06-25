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
    missed: bool = False
    gap_days: int | None = None
    calc: str | None = None
    explanation: str | None = None
    evidence: Evidence | None = None


class SearchSummary(BaseModel):
    eligible_count: int
    missed_count: int


class SearchResponse(BaseModel):
    summary: SearchSummary
    results: list[CoverageResult]
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


# ── POST /analysis/compare (API 15) v2.1 ──
class ScenarioInput(BaseModel):
    days: int
    name: str


class CompareRequest(BaseModel):
    case_id: str
    scenarios: list[ScenarioInput]


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
