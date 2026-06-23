"""리포트·체크리스트 생성 (F-04) — 서류 룰 매핑 + 스냅샷 저장."""

import uuid
from datetime import UTC, datetime

from app.core.errors import NotFoundError
from app.db import get_client


def create_report(user_id: str, case_id: str) -> dict:
    """분석 결과를 가공하여 종합 분석 리포트를 생성하고 저장합니다 (F-04)."""
    db = get_client()

    # 1. Case 정보 조회
    res_case = db.table("cases").select("*").eq("id", case_id).execute()
    if not res_case.data:
        raise NotFoundError("해당 상황 정보(Case)를 찾을 수 없습니다.")
    case = res_case.data[0]

    # 2. 분석 결과 조회
    res_analysis = db.table("analysis_results").select("*").eq("case_id", case_id).execute()
    analysis_data = res_analysis.data or []

    # 3. 리포트 본문 조립
    eligible_covers = []
    missed_covers = []

    for r in analysis_data:
        cover_info = {
            "policy": r.get("policy_name"),
            "rider": r.get("rider_name"),
            "status": r.get("status"),
            "explanation": r.get("explanation"),
            "evidence": r.get("evidence"),
        }
        if r.get("status") in ["eligible", "potential"]:
            eligible_covers.append(cover_info)
            if r.get("missed"):
                missed_covers.append(cover_info)

    # 질환별 맞춤 체크리스트 작성
    disease_name = case.get("disease_name", "")
    checklist = [
        {"task": "치료 병원에서 '진료비 세부산정내역서' 발급 받기", "done": False},
        {"task": "병원비 결제 카드 영수증 챙기기", "done": False},
    ]
    if "뇌" in disease_name or "암" in disease_name:
        checklist.append(
            {
                "task": (
                    "전문의 진단명이 기재된 '진단서' 및 '조직검사결과지' 또는 '영상판독서' 챙기기"
                ),
                "done": False,
            }
        )
    if case.get("surgery"):
        checklist.append(
            {
                "task": ("수술 일자 및 수술명 정보가 포함된 '수술확인서' 또는 '진단서' 발급 받기"),
                "done": False,
            }
        )
    admission_days_current = case.get("admission_days_current", case.get("current_days"))
    if admission_days_current and admission_days_current > 0:
        checklist.append({"task": "입원 기간이 명시된 '입퇴원확인서' 챙기기", "done": False})

    # 소멸시효 문구
    statute_txt = (
        "상법 제662조에 따라 보험금 청구권은 사고 발생일"
        "(진단일, 수술일, 퇴원일 등)로부터 3년 간 행사하지 않으면 시효로 소멸합니다."
    )

    # 면책 고지
    disclaimer_txt = (
        "본 분석 결과는 약관 원문 및 기입해주신 치료 상황을 바탕으로 "
        "AI가 자동 산출한 참고 자료입니다. 실제 보험금 지급 여부 및 "
        "상세 보장액은 보험사의 심사 결과에 따라 달라질 수 있습니다."
    )

    report_id = str(uuid.uuid4())
    report_body = {
        "summary": {
            "disease_kcd": case.get("disease_kcd"),
            "disease_name": case.get("disease_name"),
            "surgery": case.get("surgery"),
            "admission_days_current": admission_days_current,
        },
        "eligible_covers": eligible_covers,
        "missed_covers": missed_covers,
        "checklist": checklist,
        "statute_of_limitations": statute_txt,
        "disclaimer": disclaimer_txt,
        "created_at": datetime.now(UTC).isoformat(),
    }

    report_data = {
        "id": report_id,
        "case_id": case_id,
        "user_id": user_id,
        "body": report_body,
        "created_at": datetime.now(UTC).isoformat(),
    }

    db.table("reports").insert(report_data).execute()

    return {"report_id": report_id}


def get_report(report_id: str) -> dict:
    """저장된 종합 분석 리포트를 조회합니다 (SCR-06)."""
    db = get_client()

    res = db.table("reports").select("*").eq("id", report_id).execute()
    if not res.data:
        raise NotFoundError("해당 리포트를 찾을 수 없습니다.")

    report = res.data[0]
    return {"report_id": report["id"], "body": report["body"]}
