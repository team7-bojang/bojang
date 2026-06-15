"""리포트(F-04) 스키마 (SCR-06)."""

from typing import Any

from pydantic import BaseModel


class ReportCreate(BaseModel):
    case_id: str


class ReportCreated(BaseModel):
    report_id: str


class Report(BaseModel):
    report_id: str
    body: dict[str, Any]  # 상황요약·청구가능보장·비교결과·체크리스트·소멸시효·면책고지
