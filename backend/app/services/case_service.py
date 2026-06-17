import uuid
import json
from datetime import datetime, timezone
from app.db import get_client
from app.config import settings
from openai import OpenAI

def _classify_intent_llm(situation: str) -> tuple[str, str, str]:
    """LLM을 이용해 청구 상태와 추천 입력 방식을 예측합니다."""
    if not settings.openai_api_key:
        return _classify_intent_rule(situation)
        
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = f"""사용자의 현재 치료 상황 설명에 대해 다음 3가지를 판별하시오.

설명: "{situation}"

1. claim_status: 이미 다른 보험사에 청구했으면 "AFTER_CLAIM", 아직 청구하지 않았으면 "BEFORE_CLAIM", 알 수 없으면 "UNKNOWN"
2. recommended_input_method: 설명 내에 입원, 수술, MRI, CT, 조직검사 등 중증/고액 검사나 치료가 언급되어 있으면 "MEDICAL_DETAIL_STATEMENT"(세부산정내역서 추천), 단순 통원이나 결제 언급이면 "PAYMENT"(결제내역 추천)
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
            temperature=0.1
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("claim_status", "UNKNOWN"), data.get("recommended_input_method", "PAYMENT"), data.get("message", "")
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
    message = "결제 문자나 카드내역이 있다면 빠르게 확인할 수 있어요. 진료비 세부산정내역서가 있다면 더 정확한 분석이 가능해요."
    
    if any(word in situation for word in ["입원", "수술", "mri", "ct", "도수", "정밀", "뇌경색", "위암", "디스크"]):
        recommended = "MEDICAL_DETAIL_STATEMENT"
        message = "입원, 수술 또는 정밀검사가 포함되어 있네요. 진료비 세부산정내역서를 올려주시면 한도와 공제금을 정확하게 계산해 드릴게요."
        
    return claim_status, recommended, message

def create_case(user_id: str, situation: str) -> dict:
    """최초 상황 입력을 받아 분석 세션(Case)을 시작하고 의도 분석 결과를 반환합니다 (v1.5). SCR-10b 지원 범위 밖 질문 감지 포함."""
    # 지원 범위 밖 감지 (FR-10b)
    out_of_scope_keywords = ["자동차", "교통사고", "화재", "배상책임", "배상", "일상생활배상"]
    if any(kw in situation for kw in out_of_scope_keywords):
        return {
            "case_id": None,
            "initial_situation": situation,
            "claim_status": "UNKNOWN",
            "recommended_input_method": "PAYMENT",
            "available_input_methods": [],
            "out_of_scope": True,
            "message": """문의하신 내용은 현재 지원 범위 밖이에요.
저희 서비스는 질병·암·실손·상해보험 약관을 기준으로 보장 가능성을 안내합니다.
자동차·화재·배상책임 관련 청구는 사고 경위, 과실 비율, 현장 조사 등 약관 외 판단 요소가 커서 현재는 분석하지 않습니다.
질병·암·실손·상해 관련 청구 상황으로 다시 입력해 주세요."""
        }

    db = get_client()
    case_id = str(uuid.uuid4())
    
    # 의도 판정
    claim_status, rec_method, message = _classify_intent_llm(situation)
    
    # 질병명 매핑 스텁 (질문 텍스트에서 간단히 매칭)
    disease_kcd = "M51"
    disease_name = "기타 추간판 장애 (허리디스크)"
    if "뇌경색" in situation or "뇌졸중" in situation:
        disease_kcd = "I63"
        disease_name = "뇌경색증"
    elif "비염" in situation:
        disease_kcd = "J30"
        disease_name = "알레르기성 비염"
    elif "위암" in situation:
        disease_kcd = "C16"
        disease_name = "위의 악성 신생물 (위암)"

    # 기본 치료 형태 매핑
    surgery = "수술" in situation
    hosp_days = 0
    if "입원" in situation:
        # 간단한 숫자 파싱 (예: "30일 입원" -> 30)
        import re
        match = re.search(r"(\d+)\s*일\s*입원", situation)
        if match:
            hosp_days = int(match.group(1))
        else:
            hosp_days = 3 # 기본값

    case_data = {
        "id": case_id,
        "user_id": user_id,
        "disease_kcd": disease_kcd,
        "disease_name": disease_name,
        "surgery": surgery,
        "diag_days": hosp_days if hosp_days > 0 else None,
        "current_days": hosp_days if hosp_days > 0 else None,
        "policy_elapsed_days": 800, # 기본값 (대기 및 감액 통과 조건 충족용)
        "claimed_policy_ids": [],
        "initial_situation": situation,
        "claim_status": claim_status,
        "recommended_input_method": rec_method,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    db.table("cases").insert(case_data).execute()
    
    return {
        "case_id": case_id,
        "initial_situation": situation,
        "claim_status": claim_status,
        "recommended_input_method": rec_method,
        "available_input_methods": ["PAYMENT", "MEDICAL_DETAIL_STATEMENT"],
        "message": message
    }

def save_payment(user_id: str, case_id: str, payment_text: str) -> dict:
    """결제내역 텍스트를 파싱하여 Case 정보를 업데이트합니다."""
    db = get_client()
    
    # 기존 Case 조회
    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise Exception("해당 케이스를 찾을 수 없습니다.")
        
    case = res.data[0]
    
    # 텍스트 분석하여 입원일수, 수술여부, 질병명 추가 보정 (스텁)
    updates = {}
    
    # 예: "30일 입원"
    import re
    hosp_match = re.search(r"(\d+)\s*일\s*입원", payment_text)
    if hosp_match:
        days = int(hosp_match.group(1))
        updates["current_days"] = days
        updates["diag_days"] = days
        
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
    db = get_client()
    
    updates = {
        "diag_days": 14,       # 예시: 14일 입원 추출
        "current_days": 14,
        "surgery": False
    }
    db.table("cases").update(updates).eq("id", case_id).execute()
    # 최신 데이터 리로드
    res = db.table("cases").select("*").eq("id", case_id).execute()
    return res.data[0] if res.data else updates

def patch_extracted_info(user_id: str, case_id: str, info: dict) -> dict:
    """사용자가 직접 확인 및 수정한 추출 정보를 업데이트합니다."""
    db = get_client()
    
    # Pydantic 또는 요청 바디의 필드 매핑
    updates = {}
    if "disease_kcd" in info:
        updates["disease_kcd"] = info["disease_kcd"]
    if "disease_name" in info:
        updates["disease_name"] = info["disease_name"]
    if "surgery" in info:
        updates["surgery"] = info["surgery"]
    if "diag_days" in info:
        updates["diag_days"] = info["diag_days"]
    if "current_days" in info:
        updates["current_days"] = info["current_days"]
    if "claimed_policy_ids" in info:
        updates["claimed_policy_ids"] = info["claimed_policy_ids"]
    if "policy_elapsed_days" in info:
        updates["policy_elapsed_days"] = info["policy_elapsed_days"]
        
    db.table("cases").update(updates).eq("id", case_id).execute()
    return {"status": "success"}

def save_answers(user_id: str, case_id: str, answers: dict) -> dict:
    """부족 정보에 대한 추가 답변을 저장합니다."""
    db = get_client()
    
    # 답변 정보를 case 데이터에 녹여 입원/수술 정보 등으로 보완
    updates = {}
    if answers.get("surgery") is not None:
        updates["surgery"] = answers["surgery"]
    if answers.get("current_days") is not None:
        updates["current_days"] = answers["current_days"]
    if answers.get("diag_days") is not None:
        updates["diag_days"] = answers["diag_days"]
        
    db.table("cases").update(updates).eq("id", case_id).execute()
    return {"status": "success"}

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
        if c.get("current_days"):
            summary += f" ({c['current_days']}일 입원)"
        if c.get("surgery"):
            summary += " 및 수술"

        results.append({
            "case_id": c["id"],
            "created_at": c["created_at"],
            "summary": summary,
            "eligible_count": eligible_count,
            "report_id": report_id
        })
        
    return results
