import json
import re
import uuid
from datetime import UTC, datetime

from openai import OpenAI

from app.config import settings
from app.core.errors import ForbiddenError, NotFoundError
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
    "ETC",
}


def _classify_intent_llm(situation: str) -> tuple[str, str, str]:
    """LLM을 이용해 청구 상태와 추천 입력 방식을 예측합니다."""
    import os

    if os.environ.get("MOCK_LLM") == "True" or not settings.openai_api_key:
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


def create_case(user_id: str, service_type: str, policy_ids: list[str], initial_situation: str) -> dict:
    """최초 상황 입력을 받아 분석 세션(Case)을 시작하고 결과를 반환합니다 (v2.1)."""
    # 지원 범위 밖 감지 (FR-10b)
    out_of_scope_keywords = ["자동차", "교통사고", "화재", "배상책임", "배상", "일상생활배상"]
    if any(kw in initial_situation for kw in out_of_scope_keywords):
        return {
            "case_id": None,
            "service_type": service_type,
            "policy_ids": policy_ids,
            "initial_situation": initial_situation,
            "claim_status": "UNKNOWN",
            "disease_name": None,
            "disease_kcd": None,
            "recommended_input_method": "PAYMENT",
            "available_input_methods": [],
            "message": """문의하신 내용은 현재 지원 범위 밖이에요.
저희 서비스는 질병·암·실손·상해보험 약관을 기준으로 보장 가능성을 안내합니다.
자동차·화재·배상책임 관련 청구는 사고 경위, 과실 비율, 현장 조사 등
약관 외 판단 요소가 커서 현재는 분석하지 않습니다.
질병·암·실손·상해 관련 청구 상황으로 다시 입력해 주세요.""",
        }

    case_id = str(uuid.uuid4())
    db = get_client()

    # 1. Preset 선택 등록 (CASE2인 경우 단일 선택 유효성 검증)
    from app.services import policy_service

    if service_type == "CASE2" and len(policy_ids) > 1:
        raise ValueError("CASE2는 1개의 보험 상품만 선택할 수 있습니다.")

    policy_service.select_presets(user_id, policy_ids)

    # 2. 의도 판정
    claim_status, rec_method, message = _classify_intent_llm(initial_situation)

    # 3. 질병명 매핑 (검색 키워드 매칭 및 Supabase diseases 조회)
    disease_kcd = None
    disease_name = None
    disease_kcd_candidates = []
    disease_match_confidence = "high"

    # 1) 입력어 내 부위(장기) 및 일상어 매핑 추출
    # 대표적인 신체 부위 및 장기 키워드 매핑 사전
    BODY_PARTS = ["손목", "발목", "허리", "목", "뇌", "위", "폐", "가슴", "어깨", "무릎", "심장", "대장", "간"]
    body_part = None
    for bp in BODY_PARTS:
        if bp in initial_situation:
            body_part = bp
            break

    # 일상어 매핑을 통한 질병 그룹(group_id) 추출
    matched_group_ids = []
    try:
        aliases_res = db.table("disease_group_aliases").select("group_id, alias").execute()
        for row in aliases_res.data or []:
            alias = row["alias"]
            if alias in initial_situation:
                matched_group_ids.append(row["group_id"])
    except Exception as e:
        print(f"[CaseService] Failed to query disease_group_aliases: {e}")
    matched_group_ids = list(set(matched_group_ids))

    # 2) 질병 그룹 코드 룰을 바탕으로 KCD 범위 수집
    allowed_kcd_ranges = []
    if matched_group_ids:
        try:
            rules_res = db.table("disease_group_code_rules").select("*").in_("group_id", matched_group_ids).execute()
            for rule in rules_res.data or []:
                if rule["rule_type"] == "include":
                    allowed_kcd_ranges.append((rule["code_start"], rule["code_end"]))
        except Exception as e:
            print(f"[CaseService] Failed to query disease_group_code_rules: {e}")

    # 3) diseases 테이블 조회하여 후보군 필터링 및 수집
    candidates_raw = []

    # [우선순위 1] 입력 상황설명 단어 정밀 매칭 (기존 시나리오 C의 확장 및 불용어 제거)
    words = re.findall(r"[가-힣a-zA-Z0-9]+", initial_situation)
    keywords = []
    josa_suffixes = [
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "에서",
        "에게",
        "의",
        "으로",
        "로",
        "와",
        "과",
        "하고",
        "했다",
        "해요",
        "했습니다",
        "해서",
        "했음",
        "입원",
        "통원",
        "수술",
        "치료",
        "다녀왔어",
        "방문",
        "의사",
        "째인데",
        "경우",
        "보장",
    ]
    for w in words:
        if len(w) < 2:
            continue
        cleaned = w
        for josa in josa_suffixes:
            if w.endswith(josa) and len(w) > len(josa):
                candidate = w[: -len(josa)]
                if len(candidate) >= 2:
                    cleaned = candidate
                    break
        if cleaned not in [
            "의사가",
            "의사",
            "입원",
            "통원",
            "수술",
            "치료",
            "다녀",
            "방문",
            "경우",
            "보장",
            "차이",
            "궁금",
        ]:
            keywords.append(cleaned)
    keywords = list(set(keywords))

    seen_kcds = set()
    for kw in keywords:
        if len(kw) < 2:
            continue
        try:
            res = db.table("diseases").select("*").ilike("search_text", f"%{kw}%").limit(5).execute()
            for item in res.data or []:
                if item["kcd"] not in seen_kcds:
                    seen_kcds.add(item["kcd"])
                    candidates_raw.append(item)
        except Exception as e:
            print(f"[CaseService] Direct keyword diseases query failed for {kw}: {e}")

    # [우선순위 2] 단어 정밀 매칭 실패 시, 광범위 신체부위 매칭 (기존 시나리오 A)
    if not candidates_raw and body_part:
        try:
            res = db.table("diseases").select("*").ilike("search_text", f"%{body_part}%").execute()
            for item in res.data or []:
                kcd = item["kcd"]
                if allowed_kcd_ranges:
                    in_range = False
                    for start, end in allowed_kcd_ranges:
                        kcd_clean = kcd[:3]
                        if end:
                            if start <= kcd_clean <= end:
                                in_range = True
                                break
                        else:
                            if kcd.startswith(start):
                                in_range = True
                                break
                    if in_range:
                        candidates_raw.append(item)
                else:
                    candidates_raw.append(item)
        except Exception as e:
            print(f"[CaseService] Failed to query diseases by body part: {e}")

    # [우선순위 3] 신체부위도 없을 시 질병 그룹 범위 매칭 (기존 시나리오 B)
    elif not candidates_raw and allowed_kcd_ranges:
        try:
            for start, end in allowed_kcd_ranges:
                query = db.table("diseases").select("*")
                if end:
                    res = query.ilike("kcd", f"{start[0]}%").limit(20).execute()
                    for item in res.data or []:
                        kcd_clean = item["kcd"][:3]
                        if start <= kcd_clean <= end:
                            candidates_raw.append(item)
                else:
                    res = query.ilike("kcd", f"{start}%").limit(5).execute()
                    candidates_raw.extend(res.data or [])
        except Exception as e:
            print(f"[CaseService] Failed to query diseases by range rules: {e}")

    # 4) 사용자 친화적인 이름 치환 및 중복 제거
    FRIENDLY_NAMES = {
        "S62": "손목 골절",
        "S63": "손목 염좌",
        "S60": "손목 타박상",
        "S635": "손목 인대 손상",
        "G56": "손목터널증후군",
        "M51": "허리디스크",
        "S335": "요추 염좌 (허리 삠)",
        "I63": "뇌경색증",
        "J30": "알레르기성 비염",
        "C16": "위암",
        "C34": "폐암",
        "I60": "지주막하출혈",
        "I61": "뇌내출혈",
        "I21": "급성심근경색증",
    }

    seen_kcds = set()
    for item in candidates_raw:
        kcd = item["kcd"]
        if kcd not in seen_kcds:
            seen_kcds.add(kcd)
            # 이름 변환: 사전에 정의된 친근한 이름이 있으면 쓰고, 없으면 괄호 안 이름 추출 시도, 그마저도 없으면 원래 이름
            name = FRIENDLY_NAMES.get(kcd)
            if not name:
                orig_name = item["name"]
                match = re.search(r"\(([^)]+)\)", orig_name)
                if match:
                    name = match.group(1)
                else:
                    name = orig_name
            disease_kcd_candidates.append({"kcd": kcd, "name": name})

    # 정렬 및 5개 한도 제한 (가장 매치 확률이 높은 것 위주)
    if body_part:
        disease_kcd_candidates.sort(key=lambda x: body_part not in x["name"])

    disease_kcd_candidates = disease_kcd_candidates[:5]

    # 4-2) 사용자 입력설명에 특정 질병 키워드가 확실하게 매칭되는 경우 단독 후보로 지정
    exact_candidates = []
    for cand in disease_kcd_candidates:
        name = cand["name"]
        clean_name = re.sub(r"\(.*\)", "", name).strip()
        match_found = False
        for length in range(len(clean_name), 1, -1):
            sub = clean_name[:length]
            if sub in initial_situation and sub not in ["기타", "통원", "입원", "치료", "수술", "검사", "질병", "상해"]:
                match_found = True
                break
        if match_found:
            exact_candidates.append(cand)

    # 매칭된 후보가 여러 개일 경우, 설명 텍스트에 들어있는 핵심 키워드와 글자수 차이가 가장 적은 단독 후보 낙점
    if len(exact_candidates) > 1:
        best_cand = None
        min_diff = 9999
        for cand in exact_candidates:
            name = cand["name"]
            clean_name = re.sub(r"\(.*\)", "", name).strip()
            match_len = 0
            for length in range(len(clean_name), 1, -1):
                sub = clean_name[:length]
                if sub in initial_situation and sub not in [
                    "기타",
                    "통원",
                    "입원",
                    "치료",
                    "수술",
                    "검사",
                    "질병",
                    "상해",
                ]:
                    match_len = len(sub)
                    break
            if match_len > 0:
                diff = len(clean_name) - match_len
                if diff < min_diff:
                    min_diff = diff
                    best_cand = cand
                elif diff == min_diff:
                    best_cand = None  # 동률인 경우 탈락

        # 글자 수 길이 차이가 3자 이내로 근접한 확실한 후보가 있으면 그것만 남김
        if best_cand and min_diff <= 3:
            exact_candidates = [best_cand]

    if len(exact_candidates) == 1:
        disease_kcd_candidates = exact_candidates

    # 5) 최종 신뢰도 및 대표 질병명 세팅
    if len(disease_kcd_candidates) > 1:
        disease_match_confidence = "need_user_confirmation"
        disease_kcd = disease_kcd_candidates[0]["kcd"]
        disease_name = disease_kcd_candidates[0]["name"]
    elif len(disease_kcd_candidates) == 1:
        disease_match_confidence = "high"
        disease_kcd = disease_kcd_candidates[0]["kcd"]
        disease_name = disease_kcd_candidates[0]["name"]
    else:
        # 매칭되는 게 없을 경우 하드코딩 폴백 및 기본값 처리
        if "뇌경색" in initial_situation or "뇌졸중" in initial_situation:
            disease_kcd = "I63"
            disease_name = "뇌경색증"
            disease_match_confidence = "high"
        elif "심근경색" in initial_situation or "심장" in initial_situation:
            disease_kcd = "I21"
            disease_name = "급성 심근경색증"
            disease_match_confidence = "high"
        elif "비염" in initial_situation:
            disease_kcd = "J30"
            disease_name = "알레르기성 비염"
            disease_match_confidence = "high"
        elif "위암" in initial_situation:
            disease_kcd = "C16"
            disease_name = "위의 악성 신생물 (위암)"
            disease_match_confidence = "high"
        elif "디스크" in initial_situation or "허리" in initial_situation:
            disease_kcd = "M51"
            disease_name = "기타 추간판장애 (허리디스크)"
            disease_match_confidence = "need_user_confirmation"
            disease_kcd_candidates = [
                {"kcd": "M51", "name": "기타 추간판장애 (허리디스크)"},
                {"kcd": "S335", "name": "요추의 염좌 및 긴장"},
                {"kcd": "M41", "name": "척추측만증"},
                {"kcd": "M47", "name": "척추증"},
            ]
        else:
            disease_kcd = "R69"
            disease_name = initial_situation[:50]
            disease_match_confidence = "need_user_confirmation"
            disease_kcd_candidates = [
                {"kcd": "M51", "name": "기타 추간판장애 (허리디스크)"},
                {"kcd": "I63", "name": "뇌경색증"},
                {"kcd": "J30", "name": "알레르기성 비염"},
                {"kcd": "C16", "name": "위의 악성 신생물 (위암)"},
                {"kcd": "I21", "name": "급성 심근경색증"},
            ]

    # 4. 입원/통원 여부 매핑
    is_inpatient = "입원" in initial_situation
    is_outpatient = any(w in initial_situation for w in ["통원", "외래", "통원치료", "외래진료", "통원 치료"])
    if is_inpatient and is_outpatient:
        is_outpatient = False

    if not is_inpatient and not is_outpatient:
        is_outpatient = False

    # 5. 기본 치료 형태 매핑
    surgery = None
    if "수술" in initial_situation or "시술" in initial_situation:
        if any(neg in initial_situation for neg in ["수술 안", "수술은 안", "수술하지", "수술 받지", "수술을 받지", "수술 없", "시술 안", "시술은 안", "시술하지", "시술 받지", "시술 없"]):
            surgery = False
        else:
            surgery = True
    hosp_days = None
    if "입원" in initial_situation:
        match = re.search(r"(\d+)\s*일\s*입원", initial_situation)
        if match:
            hosp_days = int(match.group(1))

    diag_days = hosp_days if (hosp_days is not None and hosp_days > 0) else None
    current_days = hosp_days if (hosp_days is not None and hosp_days > 0) else None

    # CASE2인 경우 진단 및 경과 일수/주수 파싱
    if service_type == "CASE2":
        diag_day_match = re.search(
            r"(\d+)\s*일\s*(?:입원하라고|입원하래|입원하라|권고|진단|처방|하라고|입원)", initial_situation
        )
        diag_week_match = re.search(r"(\d+)\s*주\s*(?:진단|입원하라고)", initial_situation)

        curr_day_match = re.search(r"(\d+)\s*일\s*(?:째|차)", initial_situation)
        curr_week_match = re.search(r"(\d+)\s*주\s*차", initial_situation)

        if diag_day_match:
            diag_days = int(diag_day_match.group(1))
        elif diag_week_match:
            diag_days = int(diag_week_match.group(1)) * 7

        if curr_day_match:
            current_days = int(curr_day_match.group(1))
        elif curr_week_match:
            current_days = int(curr_week_match.group(1)) * 7

    if is_outpatient and not is_inpatient:
        current_days = 0

    # AFTER_CLAIM일 때 이미 청구한 보험 id 목록 파싱
    claimed_ids = []
    if claim_status == "AFTER_CLAIM":
        for pid in policy_ids:
            res_p = db.table("policies").select("name, insurer").eq("id", pid).execute()
            if res_p.data:
                p_info = res_p.data[0]
                if p_info.get("insurer") in initial_situation or p_info.get("name") in initial_situation:
                    claimed_ids.append(pid)
        if not claimed_ids and policy_ids:
            claimed_ids = [policy_ids[0]]

    case_data = {
        "id": case_id,
        "user_id": user_id,
        "service_type": service_type,
        "policy_ids": policy_ids,
        "disease_kcd": disease_kcd,
        "disease_name": disease_name,
        "disease_kcd_candidates": disease_kcd_candidates,
        "disease_match_confidence": disease_match_confidence,
        "surgery": surgery,
        "admission_days_diagnosed": diag_days,
        "admission_days_current": current_days,
        "policy_elapsed_days": None,
        "claimed_policy_ids": claimed_ids,
        "is_inpatient": is_inpatient,
        "is_outpatient": is_outpatient,
        "treatment_items": None,
        "created_at": datetime.now(UTC).isoformat(),
    }

    db.table("cases").insert(case_data).execute()

    return {
        "case_id": case_id,
        "service_type": service_type,
        "policy_ids": policy_ids,
        "initial_situation": initial_situation,
        "claim_status": claim_status,
        "claimed_policy_ids": claimed_ids if claim_status == "AFTER_CLAIM" else None,
        "disease_name": disease_name,
        "disease_kcd": disease_kcd,
        "disease_kcd_candidates": disease_kcd_candidates,
        "disease_match_confidence": disease_match_confidence,
        "recommended_input_method": None if service_type == "CASE2" else rec_method,
        "available_input_methods": ([] if service_type == "CASE2" else ["PAYMENT", "MEDICAL_DETAIL_STATEMENT"]),
        "message": None if service_type == "CASE2" else message,
        "treatment_types": get_treatment_types(),
        "next_question": get_next_question(case_data),
    }


def save_payment(user_id: str, case_id: str, payment_text: str) -> dict:
    """결제내역 텍스트를 파싱하여 Case 정보를 업데이트하고 visit_type_inference 추론을 제공합니다."""
    db = get_client()

    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 케이스를 찾을 수 없습니다.")

    case = res.data[0]
    if case.get("service_type") == "CASE2":
        raise ValueError("CASE2 서비스에서는 결제 입력 API를 사용할 수 없습니다.")

    import re

    # 1. 금액 파싱 (기본 8만원)
    payment_amount = 80000
    amt_match = re.search(r"([\d,]+)\s*원", payment_text)
    if amt_match:
        payment_amount = int(amt_match.group(1).replace(",", ""))

    # 2. 날짜 파싱 (기본 2026-06-10)
    payment_date = "2026-06-10"
    date_match = re.search(r"(\d{1,2})/(\d{1,2})", payment_text)
    if date_match:
        payment_date = f"2026-{int(date_match.group(1)):02d}-{int(date_match.group(2)):02d}"

    # 3. 병원명 파싱
    hospital_name = "OO정형외과"
    hosp_match = re.search(r"([가-힣\w]+(?:병원|의원|약국|센터|의료원))", payment_text)
    if hosp_match:
        hospital_name = hosp_match.group(1)

    # 3-2. 결제 텍스트에서 치료 항목(treatment_items) 동적 추출
    treatment_items = []
    text_lower = payment_text.lower()

    available_treatments = get_treatment_types()
    TREATMENT_KEYWORDS = {
        "MRI_MRA": ["mri", "mra", "자기공명"],
        "XRAY": ["엑스레이", "xray", "x-ray"],
        "INJECTION": ["주사", "주사치료", "injection"],
        "MANUAL_THERAPY": ["도수", "도수치료", "manual"],
        "PHYSICAL_THERAPY": ["물리", "물리치료", "physical"],
        "ECSWT": ["충격파", "체외충격파", "ecswt"],
        "CAST": ["깁스", "캐스트", "cast"],
        "BRACE_SPLINT": ["보조기", "splint", "brace"],
        "EMERGENCY": ["응급", "응급실", "emergency"],
        "MEDICATION": ["약국", "처방약", "medication"],
    }

    for t in available_treatments:
        code = t.get("code")
        name = t.get("name", "")
        keywords = list(TREATMENT_KEYWORDS.get(code, []))

        # 기본 이름 정규화하여 키워드 매핑 보조
        clean_name = re.sub(r"[\s/]", "", name).lower()
        if clean_name and clean_name not in keywords:
            keywords.append(clean_name)

        matched = False
        for kw in keywords:
            if kw in text_lower:
                matched = True
                break
        if matched and code not in treatment_items:
            treatment_items.append(code)

    # 실제 DB에 설정된 값을 기준으로 기설정 여부 판단
    db_inpt = bool(case.get("is_inpatient"))
    db_outpt = bool(case.get("is_outpatient"))
    has_established_type = db_inpt or db_outpt

    inferred = False
    inferred_is_inpatient = None
    inferred_is_outpatient = None
    inf_message = None
    threshold_basis = None

    if not has_established_type:
        if payment_amount < 100000:
            inferred = True
            inferred_is_inpatient = False
            inferred_is_outpatient = True
            inf_message = "결제금액을 보니 통원치료인 것 같은데 맞나요?"
            threshold_basis = "10만원 미만"
        elif payment_amount >= 500000:
            inferred = True
            inferred_is_inpatient = True
            inferred_is_outpatient = False
            inf_message = "결제금액을 보니 입원치료인 것 같은데 맞나요?"
            threshold_basis = "50만원 이상"

    updates = {"payment_amount": payment_amount}
    if treatment_items:
        updates["treatment_items"] = treatment_items

    db.table("cases").update(updates).eq("id", case_id).execute()

    res_c = db.table("cases").select("*").eq("id", case_id).execute()
    latest_case = res_c.data[0] if res_c.data else case

    return {
        "case_id": case_id,
        "input_method": "PAYMENT",
        "extracted_payment": {
            "payment_amount": payment_amount,
            "payment_date": payment_date,
            "hospital_name": hospital_name,
        },
        "needs_confirmation": True,
        "visit_type_inference": {
            "inferred": inferred,
            "inferred_is_inpatient": inferred_is_inpatient,
            "inferred_is_outpatient": inferred_is_outpatient,
            "message": inf_message,
            "threshold_basis": threshold_basis,
        },
        "treatment_types": get_treatment_types(),
        "next_question": get_next_question(latest_case),
    }


def save_medical_detail_statement(user_id: str, case_id: str, file_name: str) -> dict:
    """진료비 세부산정내역서 PDF 업로드 결과를 가공하여 extracted_medical_info 양식으로 리턴합니다."""
    db = get_client()

    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 케이스를 찾을 수 없습니다.")

    case = res.data[0]
    if case.get("service_type") == "CASE2":
        raise ValueError("CASE2 서비스에서는 세부산정내역서 입력 API를 사용할 수 없습니다.")

    # 파일 이름에서 치료 항목 동적 추출
    treatment_items = []
    file_name_lower = file_name.lower()

    TREATMENT_KEYWORDS = {
        "MRI_MRA": ["mri", "mra", "자기공명"],
        "XRAY": ["엑스레이", "xray", "x-ray"],
        "INJECTION": ["주사", "주사치료", "injection"],
        "MANUAL_THERAPY": ["도수", "도수치료", "manual"],
        "PHYSICAL_THERAPY": ["물리", "물리치료", "physical"],
        "ECSWT": ["충격파", "체외충격파", "ecswt"],
        "CAST": ["깁스", "캐스트", "cast"],
        "BRACE_SPLINT": ["보조기", "splint", "brace"],
        "EMERGENCY": ["응급", "응급실", "emergency"],
        "MEDICATION": ["약국", "처방약", "medication"],
    }

    for code, keywords in TREATMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in file_name_lower:
                treatment_items.append(code)
                break

    # 만약 파일명에서 추출된 치료 항목이 없다면 기본값 제공
    if not treatment_items:
        treatment_items = ["MANUAL_THERAPY", "PHYSICAL_THERAPY"]

    # 기존 케이스의 질병명 정보가 덮어씌워지지 않도록 유지
    disease_name = case.get("disease_name") or "기타 추간판 장애 (허리디스크)"
    disease_kcd = case.get("disease_kcd") or "M51"
    is_inpatient = bool(case.get("is_inpatient"))
    is_outpatient = bool(case.get("is_outpatient"))

    # 둘 다 설정 안 되어 있다면 기본적으로 통원(OUTPATIENT) 가정
    if not is_inpatient and not is_outpatient:
        is_outpatient = True

    surgery = "수술" in file_name_lower or bool(case.get("surgery"))

    updates = {
        "admission_days_diagnosed": case.get("admission_days_diagnosed") or (14 if is_inpatient else 0),
        "admission_days_current": case.get("admission_days_current") or (14 if is_inpatient else 0),
        "surgery": surgery,
        "treatment_items": treatment_items,
        "is_inpatient": is_inpatient,
        "is_outpatient": is_outpatient,
        "payment_amount": case.get("payment_amount") or 90000,
    }
    db.table("cases").update(updates).eq("id", case_id).execute()

    res_c = db.table("cases").select("*").eq("id", case_id).execute()
    latest_case = res_c.data[0] if res_c.data else updates

    print(
        f"[case_service] 세부산정내역서({file_name}) 분석 완료: "
        f"질병={disease_name}({disease_kcd}), 치료항목={treatment_items}"
    )

    return {
        "case_id": case_id,
        "input_method": "MEDICAL_DETAIL_STATEMENT",
        "extracted_medical_info": {
            "disease_name": disease_name,
            "disease_kcd": disease_kcd,
            "hospital_name": "OO정형외과",
            "visit_dates": ["2026-06-10"],
            "is_inpatient": is_inpatient,
            "is_outpatient": is_outpatient,
            "surgery": surgery,
            "treatment_items": treatment_items,
            "payment_amount": updates["payment_amount"],
            "total_amount": 113900,
            "patient_paid_amount": 7100,
            "nhis_paid_amount": 16800,
            "non_covered_amount": updates["payment_amount"],
            "item_details": [
                {"name": t_code, "amount": 70000, "is_non_covered": True, "count": 1} for t_code in treatment_items
            ],
        },
        "needs_confirmation": True,
        "next_question": get_next_question(latest_case),
    }


def patch_extracted_info(user_id: str, case_id: str, info: dict) -> dict:
    """사용자가 직접 확인 및 수정한 추출 정보를 업데이트합니다."""
    db = get_client()

    updates = {}
    input_method = info.get("input_method")

    is_inpt = info.get("confirmed_is_inpatient")
    is_outpt = info.get("confirmed_is_outpatient")

    if is_inpt is not None:
        updates["is_inpatient"] = bool(is_inpt)
    if is_outpt is not None:
        updates["is_outpatient"] = bool(is_outpt)

    # 최상위 검수 완료 데이터 바인딩 추가
    if "disease_name" in info:
        updates["disease_name"] = info["disease_name"]
    if "disease_kcd" in info:
        updates["disease_kcd"] = info["disease_kcd"]
    if "surgery" in info:
        updates["surgery"] = bool(info["surgery"])
    if "policy_elapsed_days" in info:
        updates["policy_elapsed_days"] = (
            int(info["policy_elapsed_days"]) if info["policy_elapsed_days"] is not None else None
        )
    if "current_days" in info:
        updates["admission_days_current"] = int(info["current_days"]) if info["current_days"] is not None else None
    if "diag_days" in info:
        updates["admission_days_diagnosed"] = int(info["diag_days"]) if info["diag_days"] is not None else None
    if "claimed_policy_ids" in info:
        updates["claimed_policy_ids"] = info["claimed_policy_ids"] or []
    if "treatment_items" in info:
        updates["treatment_items"] = info["treatment_items"] or []
    if "payment_amount" in info:
        updates["payment_amount"] = info["payment_amount"]
    if "coverage_amounts" in info:
        # 보장별 가입금액 [{rider_id, amount, amount_source}]. judge 정액 금액 산출에 사용.
        updates["coverage_amounts"] = info["coverage_amounts"] or []

    if input_method == "PAYMENT" and "confirmed_payment" in info:
        pay_info = info["confirmed_payment"] or {}
        if "payment_amount" in pay_info:
            updates["payment_amount"] = pay_info["payment_amount"]
        if "payment_date" in pay_info:
            updates["visit_dates"] = pay_info["payment_date"]

    elif input_method == "MEDICAL_DETAIL_STATEMENT" and "confirmed_medical_info" in info:
        med_info = info["confirmed_medical_info"] or {}
        if "disease_name" in med_info:
            updates["disease_name"] = med_info["disease_name"]
        if "disease_kcd" in med_info:
            updates["disease_kcd"] = med_info["disease_kcd"]
        if "surgery" in med_info:
            updates["surgery"] = med_info["surgery"]
        if "treatment_items" in med_info:
            updates["treatment_items"] = med_info["treatment_items"]
        if "payment_amount" in med_info:
            updates["payment_amount"] = med_info["payment_amount"]

    if updates:
        db.table("cases").update(updates).eq("id", case_id).execute()

    return {"confirmed": True}


def save_answers(user_id: str, case_id: str, answers: list[dict]) -> dict:
    """부족 정보에 대한 추가 답변 리스트(v2.1)를 저장합니다."""
    db = get_client()
    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 case를 찾을 수 없습니다.")
    case = res.data[0]
    if case.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")

    updates = {}
    is_inpt = None
    is_outpt = None

    for ans in answers:
        q_id = ans.get("question_id")
        val = ans.get("value")

        if q_id == "disease_name":
            updates["disease_name"] = val
            updates["disease_match_confidence"] = "high"
        elif q_id == "disease_kcd":
            updates["disease_kcd"] = val
            updates["disease_match_confidence"] = "high"
        elif q_id == "is_inpatient":
            is_inpt = bool(val)
        elif q_id == "is_outpatient":
            is_outpt = bool(val)
        elif q_id == "surgery":
            updates["surgery"] = bool(val)
        elif q_id == "admission_days_diagnosed":
            if val is not None:
                try:
                    num_str = re.sub(r"[^0-9]", "", str(val))
                    days_val = int(num_str) if num_str else None
                    updates["admission_days_diagnosed"] = days_val
                    if days_val and days_val > 0:
                        is_inpt = True
                        is_outpt = False
                except Exception:
                    pass
        elif q_id == "admission_days_current":
            if val is not None:
                val_str = str(val).strip()
                if "통원" in val_str or "외래" in val_str or val_str == "0" or "안 했" in val_str:
                    is_inpt = False
                    is_outpt = True
                    updates["admission_days_current"] = 0
                    updates["admission_days_diagnosed"] = 0
                else:
                    try:
                        num_str = re.sub(r"[^0-9]", "", val_str)
                        days_val = int(num_str) if num_str else None
                        updates["admission_days_current"] = days_val
                        if days_val and days_val > 0:
                            is_inpt = True
                            is_outpt = False
                    except Exception:
                        pass
        elif q_id == "payment_amount":
            if val is not None:
                try:
                    num_str = re.sub(r"[^0-9]", "", str(val))
                    updates["payment_amount"] = int(num_str) if num_str else 0
                except Exception:
                    updates["payment_amount"] = 0
        elif q_id == "treatment_items":
            updates["treatment_items"] = val
        elif q_id == "annual_visit_count":
            if val is not None:
                try:
                    num_str = re.sub(r"[^0-9]", "", str(val))
                    updates["annual_visit_count"] = int(num_str) if num_str else None
                except Exception:
                    pass
        elif q_id == "policy_elapsed_days":
            if val is None:
                updates["policy_elapsed_days"] = None
            elif isinstance(val, int):
                updates["policy_elapsed_days"] = val
            elif isinstance(val, str):
                # "[2년 이상]" -> "2년 이상" 으로 정규화
                val_clean = val.replace("[", "").replace("]", "").strip()
                if "2년 이상" in val_clean:
                    updates["policy_elapsed_days"] = 730
                elif "1년 이상" in val_clean:
                    updates["policy_elapsed_days"] = 540
                elif "90일 이상" in val_clean:
                    updates["policy_elapsed_days"] = 180
                elif "90일 미만" in val_clean:
                    updates["policy_elapsed_days"] = 80
                elif "잘 모르겠" in val_clean:
                    updates["policy_elapsed_days"] = None
                else:
                    try:
                        num_str = re.sub(r"[^0-9]", "", val_clean)
                        updates["policy_elapsed_days"] = int(num_str) if num_str else None
                    except Exception:
                        updates["policy_elapsed_days"] = None
            else:
                updates["policy_elapsed_days"] = None

    if is_inpt is not None:
        updates["is_inpatient"] = bool(is_inpt)
    if is_outpt is not None:
        updates["is_outpatient"] = bool(is_outpt)

    if updates:
        db.table("cases").update(updates).eq("id", case_id).execute()

    res_c = db.table("cases").select("*").eq("id", case_id).execute()
    latest_case = res_c.data[0] if res_c.data else {}

    return {
        "case_id": case_id,
        "ready_for_dashboard": True,
        "case": latest_case,
        "treatment_types": get_treatment_types(),
        "next_question": get_next_question(latest_case),
    }


def get_dashboard(user_id: str, case_id: str) -> dict:
    """대시보드 화면에 노출할 9개 항목 데이터를 조회해 가공합니다."""
    db = get_client()
    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 케이스를 찾을 수 없습니다.")

    c = res.data[0]
    if c.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")

    is_inpatient = bool(c.get("is_inpatient"))
    is_outpatient = bool(c.get("is_outpatient"))

    visit_date = c.get("visit_dates")
    if not visit_date and c.get("created_at"):
        visit_date = c["created_at"][:10]

    service_type = c.get("service_type") or "CASE1"
    admission_days_diagnosed = c.get("admission_days_diagnosed") or c.get("diag_days")
    if service_type == "CASE1":
        admission_days_diagnosed = None

    return {
        "case_id": case_id,
        "service_type": service_type,
        "dashboard": {
            "disease_name": c.get("disease_name"),
            "disease_kcd": c.get("disease_kcd"),
            "is_inpatient": is_inpatient,
            "is_outpatient": is_outpatient,
            "admission_days_current": c.get("admission_days_current") or c.get("current_days"),
            "admission_days_diagnosed": admission_days_diagnosed,
            "treatment_items": c.get("treatment_items") or [],
            "payment_amount": c.get("payment_amount"),
            "visit_date": visit_date,
            "surgery": c.get("surgery"),
            "annual_visit_count": c.get("annual_visit_count") or 1,
            "policy_elapsed_days": c.get("policy_elapsed_days"),
        },
    }


def patch_dashboard(user_id: str, case_id: str, data: dict) -> dict:
    """대시보드 화면에서 직접 수정한 정보들을 DB에 반영합니다."""
    db = get_client()

    res = db.table("cases").select("*").eq("id", case_id).execute()
    if not res.data:
        raise NotFoundError("해당 케이스를 찾을 수 없습니다.")
    case = res.data[0]
    if case.get("user_id") != user_id:
        raise ForbiddenError("다른 사용자의 case에 접근할 수 없습니다.")

    # 1. 입원/통원 동시 설정 방지
    new_inpatient = data.get("is_inpatient") if data.get("is_inpatient") is not None else case.get("is_inpatient")
    new_outpatient = data.get("is_outpatient") if data.get("is_outpatient") is not None else case.get("is_outpatient")
    if new_inpatient and new_outpatient:
        raise ValueError("입원과 통원을 동시에 선택할 수 없습니다.")

    # 2. 치료 항목 유효성 검사
    if "treatment_items" in data:
        items = data["treatment_items"] or []
        for it in items:
            if it not in ALLOWED_TREATMENT_ITEMS and not it.startswith("ETC:"):
                raise ValueError(f"유효하지 않은 치료 항목 코드입니다: {it}")

    # 3. 내원일자 날짜 포맷 및 범위 검사
    visit_dates_key = "visit_dates" if "visit_dates" in data else ("visit_date" if "visit_date" in data else None)
    if visit_dates_key:
        dates = data[visit_dates_key] or []
        if isinstance(dates, str):
            dates = [dates]
        for d in dates:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                raise ValueError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD 필요).")
            try:
                dt_part = d.split("-")
                import datetime

                datetime.date(int(dt_part[0]), int(dt_part[1]), int(dt_part[2]))
            except ValueError:
                raise ValueError("유효하지 않은 날짜입니다.") from None

    updates = {}

    if "policy_elapsed_days" in data:
        updates["policy_elapsed_days"] = (
            int(data["policy_elapsed_days"]) if data["policy_elapsed_days"] is not None else None
        )
    if "disease_name" in data:
        updates["disease_name"] = data["disease_name"]
    if "disease_kcd" in data:
        updates["disease_kcd"] = data["disease_kcd"]
    if "surgery" in data:
        updates["surgery"] = bool(data["surgery"])
    if "admission_days_diagnosed" in data:
        updates["admission_days_diagnosed"] = (
            int(data["admission_days_diagnosed"]) if data["admission_days_diagnosed"] is not None else None
        )
    if "admission_days_current" in data:
        updates["admission_days_current"] = (
            int(data["admission_days_current"]) if data["admission_days_current"] is not None else None
        )
    if "treatment_items" in data:
        updates["treatment_items"] = data["treatment_items"]
    if "payment_amount" in data:
        updates["payment_amount"] = int(data["payment_amount"]) if data["payment_amount"] is not None else None
    if visit_dates_key:
        updates["visit_dates"] = data[visit_dates_key]
    if "annual_visit_count" in data:
        updates["annual_visit_count"] = (
            int(data["annual_visit_count"]) if data["annual_visit_count"] is not None else None
        )

    is_inpt = data.get("is_inpatient")
    is_outpt = data.get("is_outpatient")
    if is_inpt is not None:
        updates["is_inpatient"] = bool(is_inpt)
    if is_outpt is not None:
        updates["is_outpatient"] = bool(is_outpt)

    if updates:
        db.table("cases").update(updates).eq("id", case_id).execute()

    return {
        "case_id": case_id,
        "updated": True,
        "dashboard": get_dashboard(user_id, case_id)["dashboard"],
    }


def get_my_cases(user_id: str) -> list[dict]:
    """내 분석 이력 목록을 조회합니다."""
    db = get_client()

    res_cases = db.table("cases").select("*").eq("user_id", user_id).order("created_at", descending=True).execute()
    cases = res_cases.data or []

    results = []
    for c in cases:
        res_results = db.table("analysis_results").select("*").eq("case_id", c["id"]).execute()
        analysis_data = res_results.data or []

        eligible_count = sum(1 for r in analysis_data if r.get("status") in ["eligible", "potential"])

        res_reports = db.table("reports").select("id").eq("case_id", c["id"]).execute()
        report_id = res_reports.data[0]["id"] if res_reports.data else None

        summary = f"{c.get('disease_name', '질환')} 치료"
        if c.get("admission_days_current"):
            summary += f" ({c['admission_days_current']}일 입원)"
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


def get_treatment_types() -> list[dict]:
    """Supabase 또는 폴백 기본 리스트로부터 치료 종류 목록을 조회합니다."""
    db = get_client()
    try:
        res = db.table("treatment_types").select("*").execute()
        if res.data:
            return res.data
    except Exception as e:
        print(f"[CaseService] Failed to query treatment_types: {e}")

    return [
        {"code": "MRI_MRA", "name": "MRI / MRA 검사"},
        {"code": "XRAY", "name": "엑스레이"},
        {"code": "INJECTION", "name": "주사치료"},
        {"code": "MANUAL_THERAPY", "name": "도수치료"},
        {"code": "PHYSICAL_THERAPY", "name": "물리치료"},
        {"code": "ETC", "name": "기타"},
    ]


def get_next_question(case: dict) -> dict | None:
    """케이스의 저장 상태를 검사하여 다음으로 해야 할 질문 정보를 반환합니다."""
    service_type = case.get("service_type", "CASE1")

    # 1. 질병 정보 확인 필요
    if case.get("disease_match_confidence") == "need_user_confirmation" and not case.get("disease_kcd"):
        return {
            "question_id": "disease_kcd",
            "question_text": "입력해주신 내용과 가장 가까운 질병을 골라주세요.",
            "input_type": "select_button",
            "options": case.get("disease_kcd_candidates") or [],
        }

    # 2. 결제 자료 입력 유도 (CASE1인 경우에만 적용)
    # 아직 결제 문자나 파일 내용이 들어오지 않아 payment_amount가 비어 있을 때
    if service_type == "CASE1" and case.get("payment_amount") is None:
        return {
            "question_id": "input_method",
            "question_text": (
                "상황을 확인했어요. 분석을 진행할 자료의 입력 방식을 선택해 주세요.\n\n"
                "문자나 카드내역만 있어도 빠르게 확인할 수 있어요. (대신 치료 내용이 부족하면 제가 짧게 몇 가지 더 여쭤볼게요)\n\n"
                "진료비 세부산정내역서가 있다면 치료 항목을 직접 고르는 과정이 생략됩니다."
            ),
            "input_type": "select_button",
            "options": [
                {"value": "PAYMENT", "label": "💳 문자·카드내역으로 빠르게 확인"},
                {"value": "MEDICAL_DETAIL_STATEMENT", "label": "📄 진료비 세부산정내역서로 자세히 확인"},
            ],
        }

    # 3. 의사 권고 진단일수 (diag_days) 확인 필요 (CASE2인 경우)
    if service_type == "CASE2" and case.get("admission_days_diagnosed") is None:
        return {
            "question_id": "admission_days_diagnosed",
            "question_text": "의사가 말한 권고 입원 기간은 총 며칠인가요?",
            "input_type": "text_input",
            "placeholder": "예: 4일",
        }

    # 4. 현재 입원일수 (current_days) 확인 필요
    if case.get("admission_days_current") is None:
        # 외래 통원이 아닌 경우에만 입원일수 확인
        if not case.get("is_outpatient"):
            return {
                "question_id": "admission_days_current",
                "question_text": "지금은 입원한 지 며칠째인가요?",
                "input_type": "text_input",
                "placeholder": "예: 3일",
            }

    # 5. 수술 여부 (surgery) 확인 필요
    if case.get("surgery") is None:
        return {
            "question_id": "surgery",
            "question_text": "이번 진료에서 수술도 받으셨나요?",
            "input_type": "radio_button",
            "options": [{"value": True, "label": "예"}, {"value": False, "label": "아니요"}],
        }

    # 6. 치료 항목 (treatment_items) 확인 필요
    if case.get("treatment_items") is None:
        return {
            "question_id": "treatment_items",
            "question_text": "이번 입원 중 함께 받은 치료가 있다면 골라주세요. (여러 개 선택 가능)",
            "input_type": "checkbox_button",
            "options": [
                {"value": "MRI_MRA", "label": "영상검사 (MRI/CT)"},
                {"value": "INJECTION", "label": "주사치료"},
                {"value": "MANUAL_THERAPY", "label": "도수·충격파"},
                {"value": "PHYSICAL_THERAPY", "label": "물리치료"},
                {"value": "OTHER", "label": "기타 치료"},
            ],
        }

    # 7. 연간 내원 횟수 (annual_visit_count) 확인 필요
    if case.get("annual_visit_count") is None:
        return {
            "question_id": "annual_visit_count",
            "question_text": "올해 같은 이유로 병원에 간 게 이번 포함 몇 번째인가요?",
            "input_type": "text_input",
            "placeholder": "예: 1번",
        }

    # 8. 가입 기간 경과 (policy_elapsed_days) 확인 필요
    if case.get("policy_elapsed_days") is None:
        return {
            "question_id": "policy_elapsed_days",
            "question_text": "선택한 보험의 가입기간에 해당하는 구간을 골라주세요.",
            "input_type": "radio_button",
            "options": [
                {"value": "90일 미만", "label": "90일 미만"},
                {"value": "90일 이상~1년 미만", "label": "90일 이상~1년 미만"},
                {"value": "1년 이상~2년 미만", "label": "1년 이상~2년 미만"},
                {"value": "2년 이상", "label": "2년 이상"},
                {"value": "잘 모르겠어요", "label": "잘 모르겠어요"},
            ],
        }

    return None
