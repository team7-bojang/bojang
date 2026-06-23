import json
import re
import uuid
from datetime import date

from openai import OpenAI

from app.config import settings
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.db import get_client

ALLOWED_TREATMENT_ITEMS = {
    "MRI_MRA",
    "CT",
    "XRAY",
    "MANUAL_THERAPY",
    "PHYSICAL_THERAPY",
    "ECSWT",
    "INJECTION",
    "MEDICATION",
    "CAST",
    "BRACE_SPLINT",
    "EMERGENCY",
    "OTHER",
}


def _classify_intent_llm(situation: str) -> tuple[str, str, str]:
    """LLM을 이용해 청구 상태와 추천 입력 방식을 예측합니다."""
    if not settings.openai_api_key:
        return _classify_intent_rule(situation)

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = f"""사용자의 현재 치료 상황 설명에 대해 다음 3가지를 판별하시오.

설명: "{situation}"

1. claim_status: 이미 다른 보험사에 청구했으면 "AFTER_CLAIM",
   아직 청구하지 않았으면 "BEFORE_CLAIM", 알 수 없으면 "UNKNOWN"
2. recommended_input_method: 설명 내에 입원, 수술, MRI, CT, 조직검사 등
   중증/고액 검사나 치료가 언급되어 있으면 "MEDICAL_DETAIL_STATEMENT"(세부산정내역서 추천),
   단순 통원이나 결제 언급이면 "PAYMENT"(결제내역 추천)
3. message: 사용자를 위한 1~2문장의 친절한 추천 이유 설명 (한글)

답변은 반드시 아래 형식의 JSON으로만 출력하시오.
{{
  "claim_status": "BEFORE_CLAIM" | "AFTER_CLAIM" | "UNKNOWN",
  "recommended_input_method": "PAYMENT" | "MEDICAL_DETAIL_STATEMENT",
  "message": "..."
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(response.choices[0].message.content)
        return (
            data.get("claim_status", "UNKNOWN"),
            data.get("recommended_input_method", "PAYMENT"),
            data.get("message", ""),
        )
    except Exception as e:
        print(f"[CaseService] LLM intent classification failed: {e}")
        return _classify_intent_rule(situation)


def _classify_intent_rule(situation: str) -> tuple[str, str, str]:
    """간단한 규칙 기반 의도 분류 및 추천 방식 판별 (LLM 실패 시 폴백)."""
    # 1. 청구 상태
    claim_status = "BEFORE_CLAIM"
    if any(word in situation for word in ["이미 청구", "청구했", "돈 받았", "보험금 청구"]):
        claim_status = "AFTER_CLAIM"
    elif "청구" in situation:
        claim_status = "UNKNOWN"

    # 2. 추천 입력 방식
    recommended = "PAYMENT"
    message = (
        "결제 문자나 카드내역이 있다면 빠르게 확인할 수 있어요. "
        "진료비 세부산정내역서가 있다면 더 정확한 분석이 가능해요."
    )

    if any(word in situation for word in ["입원", "수술", "mri", "ct", "도수", "정밀", "뇌경색", "위암", "디스크"]):
        recommended = "MEDICAL_DETAIL_STATEMENT"
        message = (
            "입원, 수술 또는 정밀검사가 포함되어 있네요. "
            "진료비 세부산정내역서를 올려주시면 한도와 공제금을 정확하게 계산해 드릴게요."
        )

    return claim_status, recommended, message


def create_case(user_id: str, service_type: str, policy_ids: list[str], situation: str) -> dict:
    """최초 상황 입력을 받아 분석 세션(Case)을 시작하고 의도 분석 결과를 반환합니다 (4-7).
    SCR-10b 지원 범위 밖 질문 감지 포함.
    """
    if service_type not in ("CASE1", "CASE2"):
        raise ValidationError("service_type은 CASE1 또는 CASE2여야 합니다.")
    if not policy_ids:
        raise ValidationError("policy_ids는 1개 이상 선택해야 합니다.")
    if service_type == "CASE2" and len(policy_ids) > 1:
        raise ValidationError("CASE2는 보험을 1개만 선택할 수 있습니다.")
    if not situation:
        raise ValidationError("initial_situation은 필수입니다.")

    db = get_client()

    policies_res = db.table("policies").select("id, insurer, user_id").execute()
    policies_by_id = {p["id"]: p for p in (policies_res.data or [])}
    insurer_by_id = {pid: policy.get("insurer") for pid, policy in policies_by_id.items()}
    missing_ids = [pid for pid in policy_ids if pid not in insurer_by_id]
    if missing_ids:
        raise NotFoundError(f"존재하지 않는 보험 id가 포함되어 있습니다: {missing_ids}")
    forbidden_ids = [pid for pid in policy_ids if policies_by_id[pid].get("user_id") != user_id]
    if forbidden_ids:
        raise ForbiddenError("본인이 등록한 보험만 분석할 수 있습니다.")

    # 지원 범위 밖 감지 (FR-10b)
    out_of_scope_keywords = ["자동차", "교통사고", "화재", "배상책임", "배상", "일상생활배상"]
    if any(kw in situation for kw in out_of_scope_keywords):
        return {
            "case_id": None,
            "service_type": service_type,
            "policy_ids": policy_ids,
            "initial_situation": situation,
            "claim_status": "UNKNOWN",
            "claimed_policy_ids": None,
            "disease_name": None,
            "disease_kcd": None,
            "recommended_input_method": "PAYMENT",
            "available_input_methods": [],
            "out_of_scope": True,
            "message": """문의하신 내용은 현재 지원 범위 밖이에요.
저희 서비스는 질병·암·실손·상해보험 약관을 기준으로 보장 가능성을 안내합니다.
자동차·화재·배상책임 관련 청구는 사고 경위, 과실 비율, 현장 조사 등
약관 외 판단 요소가 커서 현재는 분석하지 않습니다.
질병·암·실손·상해 관련 청구 상황으로 다시 입력해 주세요.""",
        }

    case_id = str(uuid.uuid4())

    # 의도 판정
    claim_status, rec_method, message = _classify_intent_llm(situation)

    # 질병명 매핑 스텁 (질문 텍스트에서 간단히 매칭). 불명확하면 null (챗봇이 별도 질문, 명세 4-7)
    disease_kcd = None
    disease_name = None
    if "뇌경색" in situation or "뇌졸중" in situation:
        disease_kcd, disease_name = "I63", "뇌경색증"
    elif "비염" in situation:
        disease_kcd, disease_name = "J30", "알레르기성 비염"
    elif "위암" in situation:
        disease_kcd, disease_name = "C16", "위의 악성 신생물 (위암)"
    elif "디스크" in situation or "허리" in situation:
        disease_kcd, disease_name = "M51", "기타 추간판 장애 (허리디스크)"

    # 이미 청구한 보험 추정: 상황 텍스트에 등장하는 보험사명으로 매칭 (스텁)
    claimed_policy_ids = None
    if claim_status == "AFTER_CLAIM":
        matched = [pid for pid in policy_ids if insurer_by_id.get(pid) and insurer_by_id[pid] in situation]
        claimed_policy_ids = matched or list(policy_ids)

    # 기본 치료 형태 매핑
    surgery = "수술" in situation
    hosp_days = None
    if "입원" in situation:
        match = re.search(r"(\d+)\s*일\s*입원", situation)
        hosp_days = int(match.group(1)) if match else 3  # 숫자가 없으면 기본값

    case_data = {
        "id": case_id,
        "user_id": user_id,
        "service_type": service_type,
        "policy_ids": policy_ids,
        "disease_kcd": disease_kcd,
        "disease_name": disease_name or "",  # cases.disease_name은 NOT NULL — 불명확 시 빈 문자열로 저장
        "surgery": surgery,
        "admission_days_diagnosed": hosp_days,
        "admission_days_current": hosp_days,
        "policy_elapsed_days": None,
        "claimed_policy_ids": claimed_policy_ids or [],
    }

    db.table("cases").insert(case_data).execute()

    if service_type == "CASE2":
        recommended_input_method, available_input_methods, message_out = None, [], None
    else:
        recommended_input_method = rec_method
        available_input_methods = ["PAYMENT", "MEDICAL_DETAIL_STATEMENT"]
        message_out = message

    return {
        "case_id": case_id,
        "service_type": service_type,
        "policy_ids": policy_ids,
        "initial_situation": situation,
        "claim_status": claim_status,
        "claimed_policy_ids": claimed_policy_ids,
        "disease_name": disease_name,
        "disease_kcd": disease_kcd,
        "recommended_input_method": recommended_input_method,
        "available_input_methods": available_input_methods,
        "message": message_out,
    }


def save_payment(user_id: str, case_id: str, payment_text: str) -> dict:
    """결제내역 텍스트를 파싱하여 Case 정보를 업데이트합니다."""
    case = _get_owned_case(user_id, case_id)
    db = get_client()

    # 텍스트 분석하여 입원일수, 수술여부, 질병명 추가 보정 (스텁)
    updates = {}

    hosp_match = re.search(r"(\d+)\s*일\s*입원", payment_text)
    if hosp_match:
        days = int(hosp_match.group(1))
        updates["admission_days_current"] = days
        updates["admission_days_diagnosed"] = days

    if "수술" in payment_text:
        updates["surgery"] = True

    if updates:
        db.table("cases").update(updates).eq("id", case_id).execute()
        # 최신 데이터 리로드
        res = db.table("cases").select("*").eq("id", case_id).execute()
        case = res.data[0]

    return case


def save_medical_detail_statement(user_id: str, case_id: str, file_name: str) -> dict:
    """진료비 세부산정내역서 PDF 업로드 분석 결과를 Case에 업데이트합니다 (스텁)."""
    _get_owned_case(user_id, case_id)
    db = get_client()

    updates = {
        "admission_days_diagnosed": 14,  # 예시: 14일 입원 추출
        "admission_days_current": 14,
        "surgery": False,
    }
    db.table("cases").update(updates).eq("id", case_id).execute()
    # 최신 데이터 리로드
    res = db.table("cases").select("*").eq("id", case_id).execute()
    return res.data[0] if res.data else updates


def patch_extracted_info(user_id: str, case_id: str, info: dict) -> dict:
    """사용자가 직접 확인 및 수정한 추출 정보를 업데이트합니다 (4-10)."""
    case = _get_owned_case(user_id, case_id)

    allowed = (
        "disease_kcd",
        "disease_name",
        "is_inpatient",
        "is_outpatient",
        "surgery",
        "admission_days_diagnosed",
        "admission_days_current",
        "treatment_items",
        "payment_amount",
        "visit_dates",
        "claimed_policy_ids",
        "policy_elapsed_days",
    )
    updates = {k: v for k, v in info.items() if k in allowed}
    _validate_case_updates(case, updates)
    if updates:
        get_client().table("cases").update(updates).eq("id", case_id).execute()

    return {"case_id": case_id, "confirmed": True}


def save_answers(user_id: str, case_id: str, answers: list[dict]) -> dict:
    """챗봇 추가 질문 답변을 저장합니다 (4-11). question_id/value 배열 구조."""
    case = _get_owned_case(user_id, case_id)

    allowed_fields = {
        "disease_name",
        "disease_kcd",
        "is_inpatient",
        "is_outpatient",
        "surgery",
        "admission_days_diagnosed",
        "admission_days_current",
        "treatment_items",
        "annual_visit_count",
        "policy_elapsed_days",
    }
    updates = {}
    for item in answers:
        qid = item.get("question_id")
        val = item.get("value")
        if qid in allowed_fields:
            updates[qid] = val

    _validate_case_updates(case, updates)
    if updates:
        get_client().table("cases").update(updates).eq("id", case_id).execute()

    return {"case_id": case_id, "ready_for_dashboard": True}


def _get_owned_case(user_id: str, case_id: str) -> dict:
    db = get_client()
    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 case를 찾을 수 없습니다.")
    case = res.data[0]
    if case.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")
    return case


def _validate_case_updates(case: dict, updates: dict) -> None:
    """DB 제약 위반을 요청 단계에서 검증해 500 대신 400을 반환한다."""
    if updates.get("disease_name", case.get("disease_name")) is None:
        raise ValidationError("disease_name은 null로 변경할 수 없습니다.")

    for field in ("is_inpatient", "is_outpatient", "surgery"):
        value = updates.get(field)
        if value is not None and not isinstance(value, bool):
            raise ValidationError(f"{field}은 boolean이어야 합니다.")

    is_inpatient = updates.get("is_inpatient", case.get("is_inpatient", False))
    is_outpatient = updates.get("is_outpatient", case.get("is_outpatient", False))
    if is_inpatient and is_outpatient:
        raise ValidationError("입원과 통원을 동시에 선택할 수 없습니다.")

    non_negative_fields = (
        "admission_days_diagnosed",
        "admission_days_current",
        "payment_amount",
        "annual_visit_count",
        "policy_elapsed_days",
    )
    for field in non_negative_fields:
        value = updates.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValidationError(f"{field}은 정수여야 합니다.")
        if value is not None and value < 0:
            raise ValidationError(f"{field}은 0 이상이어야 합니다.")

    for field in ("treatment_items", "visit_dates", "claimed_policy_ids"):
        value = updates.get(field)
        if value is not None and not isinstance(value, list):
            raise ValidationError(f"{field}은 배열이어야 합니다.")

    treatment_items = updates.get("treatment_items")
    if treatment_items is not None:
        invalid_items = sorted(set(treatment_items) - ALLOWED_TREATMENT_ITEMS)
        if invalid_items:
            raise ValidationError(f"허용되지 않은 treatment_items 코드입니다: {invalid_items}")

    visit_dates = updates.get("visit_dates")
    if visit_dates is not None:
        try:
            for value in visit_dates:
                if not isinstance(value, str):
                    raise TypeError
                date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("visit_dates는 YYYY-MM-DD 형식의 날짜 배열이어야 합니다.") from exc


def _build_dashboard(case: dict) -> dict:
    """case 레코드를 대시보드 9개 항목으로 정규화합니다 (4-12).

    diag_days/current_days 는 004 마이그레이션에서 admission_days_diagnosed/
    admission_days_current 로 rename 되었으므로, 마이그레이션 이전에 저장된
    case도 읽을 수 있도록 구컬럼명을 폴백으로 둔다.
    """
    return {
        "disease_name": case.get("disease_name"),
        "disease_kcd": case.get("disease_kcd"),
        "is_inpatient": case.get("is_inpatient", False),
        "is_outpatient": case.get("is_outpatient", False),
        "admission_days_current": case.get("admission_days_current", case.get("current_days")),
        "admission_days_diagnosed": case.get("admission_days_diagnosed", case.get("diag_days")),
        "treatment_items": case.get("treatment_items") or [],
        "payment_amount": case.get("payment_amount"),
        "visit_dates": case.get("visit_dates") or [],
        "surgery": case.get("surgery", False),
        "annual_visit_count": case.get("annual_visit_count"),
        "policy_elapsed_days": case.get("policy_elapsed_days"),
    }


def get_dashboard(user_id: str, case_id: str) -> dict:
    """대시보드 항목을 조회합니다 (4-12)."""
    case = _get_owned_case(user_id, case_id)
    return {
        "case_id": case_id,
        "service_type": case.get("service_type"),
        "dashboard": _build_dashboard(case),
    }


def patch_dashboard(user_id: str, case_id: str, updates: dict) -> dict:
    """대시보드 항목을 직접 수정합니다 (4-13). 보낸 필드만 갱신한다."""
    case = _get_owned_case(user_id, case_id)

    changes = dict(updates)
    _validate_case_updates(case, changes)
    if changes:
        db = get_client()
        db.table("cases").update(changes).eq("id", case_id).execute()
        case.update(changes)

    return {
        "case_id": case_id,
        "updated": True,
        "dashboard": _build_dashboard(case),
    }


def get_my_cases(user_id: str) -> list[dict]:
    """내 분석 이력 목록을 조회합니다."""
    db = get_client()

    # 1. 사용자의 케이스 이력 조회
    res_cases = db.table("cases").select("*").eq("user_id", user_id).order("created_at", descending=True).execute()
    cases = res_cases.data or []

    results = []
    for c in cases:
        # 각 case에 대한 분석 결과(eligible_count 등) 카운팅
        res_results = db.table("analysis_results").select("*").eq("case_id", c["id"]).execute()
        analysis_data = res_results.data or []

        eligible_count = sum(1 for r in analysis_data if r.get("status") in ["eligible", "potential"])

        # 리포트 존재 여부 조회
        res_reports = db.table("reports").select("id").eq("case_id", c["id"]).execute()
        report_id = res_reports.data[0]["id"] if res_reports.data else None

        # summary 텍스트 작성
        summary = f"{c.get('disease_name', '질환')} 치료"
        admission_days_current = c.get("admission_days_current", c.get("current_days"))
        if admission_days_current:
            summary += f" ({admission_days_current}일 입원)"
        if c.get("surgery"):
            summary += " 및 수술"

        results.append(
            {
                "case_id": c["id"],
                "created_at": c["created_at"],
                "summary": summary,
                "eligible_count": eligible_count,
                "report_id": report_id,
            }
        )

    return results
