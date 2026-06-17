"""riders v1.2 스키마 (pydantic) — 파싱 출력 검증용.
Flask API의 pydantic 모델(Swagger)과 단일 소스로 공유한다.

설계 원칙(v1.2): 전량 파싱에서 다양한 보장 유형(진단비·수술비·사망보험금·
통원비 등)이 나오므로, enum을 좁게 강제해 데이터를 '버리지' 않는다.
- 권장값은 description으로 안내하되, 벗어난 값도 경고만 남기고 보존한다.
- 파싱 단계의 목표는 '원문을 구조화해 담는 것'이고, 값 정합성은 검수(verified) 단계의 몫.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 권장 enum (강제 아님 — 검수 시 이 값으로 정규화)
TRIGGER_TYPES = ["입원", "수술", "진단", "통원", "내원", "골절", "치료", "사망", "후유장해", "기타"]
UNIT_TYPES = ["1일당", "1회당", "일시금", "기타"]
LIMIT_SCOPES = [
    "per_hospitalization",
    "annual",
    "daily",
    "same_cause_window",
    "per_surgery",
    "per_diagnosis",
    "per_visit",
    "lifetime",
    "기타",
]
LIMIT_UNITS = ["days", "count", "krw"]

# claim_rule 권장값 (실손 등 정률·공제형 보장의 judge() 계산용 — 정액 보장은 claim_rule=null)
MEDICAL_CATEGORIES = ["급여", "비급여", "3대비급여"]
CAUSE_TYPES = ["상해", "질병", "상해/질병"]
VISIT_TYPES = ["입원", "통원", "치료"]
DEDUCTIBLE_TYPES = ["fixed", "max", "by_table", "from_policy"]


class Boundary(BaseModel):
    condition_days: int = Field(0, description="자격 경계 일수 (예: 4 = 4일 이상). 없으면 0")
    effect: str = ""

    @field_validator("condition_days", mode="before")
    @classmethod
    def _none_to_zero(cls, v):
        return 0 if v is None else v


class Limit(BaseModel):
    # str로 받아 어떤 값이든 보존 (검수 시 정규화). 권장값: LIMIT_SCOPES
    scope: str = Field(..., description=f"권장: {LIMIT_SCOPES}")
    unit: str = Field(..., description=f"권장: {LIMIT_UNITS}")
    value: int | None = None
    note: str | None = None


class Reduction(BaseModel):
    until_elapsed_days: int | None = Field(None, description="가입 후 N일 이내 감액")
    rate: float | None = Field(None, description="지급 비율 (0.5 = 50%)")
    note: str | None = None


class Deductible(BaseModel):
    """공제 규칙 (실손 등). claim_rule.deductible로만 사용.

    type별 의미:
      - fixed:       value원 정액 공제
      - max:         max(value, covered*rate) — "N원과 X% 중 큰 금액"
      - by_table:    병원급 등 표에 따라 달라짐 — 검수 시 세분화 (value/rate 비워둠)
      - from_policy: 약관에 공제가 있으나 값 미확정 — 검수 시 확정

    extra="forbid": value/rate는 계산에 직접 쓰이므로, rat 같은 오타가
    조용히 버려지지 않도록 미정의 필드를 에러로 잡는다.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description=f"권장: {DEDUCTIBLE_TYPES}")
    value: int | None = Field(None, description="정액 공제액(원) 또는 max의 하한")
    rate: float | None = Field(None, description="정률 공제(0.3=30%) — max에서 사용")
    note: str | None = None


class ClaimRule(BaseModel):
    """judge() 계산용 규칙. 정률·공제형 보장(실손 등)에만 채우고,
    정액 보장(진단비·입원일당 등)은 rider.claim_rule=null로 둔다.

    기존 unit_basis(사람이 읽는 서술)·limits(한도)는 그대로 두고,
    이 필드는 '기계가 금액을 계산'하는 데 필요한 핵심만 구조화한다.

    extra="forbid": 사람이 정리하는 영역이므로 오타·미정의 필드(_review 등)를
    조용히 버리지 않고 에러로 즉시 잡는다.
    """

    model_config = ConfigDict(extra="forbid")

    coverage_kind: str = Field("실손", description="보장 종류")
    cause_type: str | None = Field(None, description=f"권장: {CAUSE_TYPES}")
    medical_category: str | None = Field(None, description=f"권장: {MEDICAL_CATEGORIES}")
    visit_type: str | None = Field(None, description=f"권장: {VISIT_TYPES}")
    benefit_item: str | None = Field(None, description="세부 항목명(상급병실료 차액·도수치료 등)")
    reimbursement_rate: float = Field(
        1.0, description="보상비율(0.8/0.7/0.5). 공제 후 전액이면 1.0"
    )
    deductible: Deductible | None = None
    formula: str = Field("", description="계산식 — covered_amount 기준. 예: covered_amount * 0.8")
    review_note: str | None = Field(
        None, description="검수자에게 남기는 메모 (공제 유무 확인 등). judge()는 무시"
    )


class Source(BaseModel):
    article: str = ""
    page: int = Field(default=0, description="약관 PDF 페이지 번호")
    raw_text: str = Field(default="", description="조항 원문 — 인용 검증용. 요약·수정 금지")

    @field_validator("article", "raw_text", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return str(v)
        return str(v)

    @field_validator("page", mode="before")
    @classmethod
    def _coerce_page(cls, v):
        # "p.47", "47-48" 등 비정수 입력 방어
        if v is None:
            return 0
        if isinstance(v, int):
            return v
        import re

        m = re.search(r"\d+", str(v))
        return int(m.group()) if m else 0


class Rider(BaseModel):
    """보장 단위 (주계약 보장 + 특약) — riders 테이블 1행."""

    name: str = ""
    is_main: bool = False
    trigger_type: str = Field("기타", description=f"권장: {TRIGGER_TYPES}")
    trigger_detail: str = ""
    unit_amount: int | None = Field(
        None, description="약관에 금액이 숫자로 명시된 경우만. '보험가입금액' 기준이면 null"
    )
    unit_type: str = Field("기타", description=f"권장: {UNIT_TYPES}")
    unit_basis: str | None = None
    boundaries: list[Boundary] = []
    deduct_days: int = Field(0, description="지급 시작 offset (예: 3 = 4일째부터). 없으면 0")
    limits: list[Limit] = []
    waiting_period_days: int | None = None
    reductions: list[Reduction] = []
    exclusions: list[str] = []
    claim_rule: ClaimRule | None = Field(
        None, description="정률·공제형 보장(실손 등)의 judge() 계산 규칙. 정액 보장은 null"
    )
    source_pages: list[int] = Field(
        default_factory=list,
        description="병합된 보장의 출처 페이지들 (실손처럼 여러 페이지 합친 경우 근거 추적용)",
    )
    source: Source = Field(default_factory=Source)
    verified: bool = Field(False, description="수동 검수 통과 여부 — 파싱 출력은 항상 False")

    @field_validator("deduct_days", mode="before")
    @classmethod
    def _deduct_none_to_zero(cls, v):
        return 0 if v is None else v

    @field_validator("trigger_type", "unit_type", mode="before")
    @classmethod
    def _type_none_to_default(cls, v):
        return "기타" if v is None or v == "" else v

    @field_validator("trigger_detail", mode="before")
    @classmethod
    def _coerce_detail_to_str(cls, v):
        # LLM이 입원/통원 구분 등을 dict·list로 줄 수 있음 → 문자열로 평탄화
        if v is None:
            return ""
        if isinstance(v, dict):
            return " / ".join(f"{k}: {val}" for k, val in v.items())
        if isinstance(v, list):
            return " / ".join(str(x) for x in v)
        return str(v)

    @field_validator("name", "unit_basis", mode="before")
    @classmethod
    def _coerce_optional_str(cls, v):
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return str(v)
        return str(v)

    @field_validator("exclusions", mode="before")
    @classmethod
    def _coerce_exclusions(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            v = [v]
        out = []
        for item in v:
            if isinstance(item, (dict, list)):
                out.append(str(item))
            elif item is not None:
                out.append(str(item))
        return out

    def warnings(self) -> list[str]:
        """권장 enum 이탈을 경고로 수집 (검수 안내용 — 실패시키지 않음)."""
        w = []
        if self.trigger_type not in TRIGGER_TYPES:
            w.append(f"trigger_type 비표준값: '{self.trigger_type}'")
        if self.unit_type not in UNIT_TYPES:
            w.append(f"unit_type 비표준값: '{self.unit_type}'")
        for i, lim in enumerate(self.limits):
            if lim.scope not in LIMIT_SCOPES:
                w.append(f"limits[{i}].scope 비표준값: '{lim.scope}'")
            if lim.unit not in LIMIT_UNITS:
                w.append(f"limits[{i}].unit 비표준값: '{lim.unit}'")
        cr = self.claim_rule
        if cr is not None:
            if cr.medical_category and cr.medical_category not in MEDICAL_CATEGORIES:
                w.append(f"claim_rule.medical_category 비표준값: '{cr.medical_category}'")
            if cr.cause_type and cr.cause_type not in CAUSE_TYPES:
                w.append(f"claim_rule.cause_type 비표준값: '{cr.cause_type}'")
            if cr.deductible and cr.deductible.type not in DEDUCTIBLE_TYPES:
                w.append(f"claim_rule.deductible.type 비표준값: '{cr.deductible.type}'")
            # 이중차감 휴리스틱: 비율<1 + 공제 동시 + formula에 둘 다 곱셈/뺄셈이면 검수 경고
            if cr.reimbursement_rate < 1.0 and cr.deductible is not None:
                w.append(
                    "claim_rule: reimbursement_rate<1 과 deductible 동시 — "
                    "이중차감 아닌지 formula 확인"
                )
        return w


class ParseResult(BaseModel):
    riders: list[Rider] = []
