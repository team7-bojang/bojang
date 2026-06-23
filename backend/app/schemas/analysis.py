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


class SearchRequest(BaseModel):
    case_id: str


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

