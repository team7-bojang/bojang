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
class CompareRequest(BaseModel):
    case_id: str
    current_days: int
    target_days: int


class SliderInfo(BaseModel):
    min: int
    max: int
    current: int
    target: int
    breakpoints: list[int]


class CompareScenario(BaseModel):
    days: int
    status: str
    type: str  # "base" | "special"
    label: str
    calc: str | None = None
    amount_note: str | None = None
    gap_days: int | None = None


class CompareEvidence(BaseModel):
    article_no: str | None = None
    page: int | None = None
    quote: str | None = None


class CompareRiderResult(BaseModel):
    rider_name: str
    policy_name: str
    insurer: str
    verified: bool
    scenarios: list[CompareScenario] | None = None
    base_calc: str | None = None
    evidence: CompareEvidence | None = None


class CompareResponse(BaseModel):
    has_special_coverage: bool
    top_message: str
    missed_amount_note: str | None = None
    slider: SliderInfo | None = None
    comparison: list[CompareRiderResult]
    disclaimer: str
    notice: str | None = None


