"""리포트(F-04) 스키마 (SCR-06)."""

from typing import Any

from pydantic import BaseModel


class ReportCreate(BaseModel):
    case_id: str


class ReportCreated(BaseModel):
    report_id: str

    model_config = {"json_schema_extra": {"example": {"report_id": "b7c8e34d-1111-2222-3333-444455556666"}}}


class Report(BaseModel):
    report_id: str
    body: dict[str, Any]  # 상황요약·청구가능보장·비교결과·체크리스트·소멸시효·면책고지

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_id": "b7c8e34d-1111-2222-3333-444455556666",
                "body": {
                    "situation_summary": "뇌경색증으로 5일 입원 치료.",
                    "claimable_coverages": [
                        {"rider": "뇌혈관질환 진단비 특약", "amount": "2,000만원", "status": "eligible"}
                    ],
                    "checklist": ["진단서 발급", "입퇴원확인서 발급"],
                    "limitation_notice": "보험금 청구권 소멸시효는 3년입니다.",
                    "disclaimer": "본 결과는 약관 원문 기반 참고용이며 최종 지급은 보험사 심사에 따릅니다.",
                },
            }
        }
    }
