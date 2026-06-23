import numpy as np

from app.db import get_client
from app.rag.embedder import embed


def clean_for_match(text: str) -> str:
    if not text:
        return ""
    # 공백, 성, 증, 특약명 등 제거하여 유연한 매칭 지원
    return text.replace(" ", "").replace("성", "").replace("증", "").replace("특별약관", "").replace("특약", "")



class Retriever:
    def __init__(self):
        # get_client()를 통해 Real/Mock Supabase 연동
        self.db = get_client()

    def search(
        self, query: str, policy_ids: list[str] = None, trigger_type: str = None, disease_kcd: str = None, k: int = 5
    ) -> list[dict]:
        """쿼리와 유사한 약관 청크를 검색합니다.

        검색 로직: 메타데이터 필터(policy_ids + trigger_type) + 벡터 유사도 + 키워드 가산점
        """
        # 1. 쿼리 임베딩
        q_emb = None
        try:
            embs = embed([query])
            if embs:
                q_emb = embs[0]
        except Exception as e:
            print(f"[Retriever] Failed to embed query: {e}")

        # 1.5. 확정된 질병 코드(KCD)가 있을 경우 DB Rules 및 Groups를 동적으로 연동하여 가산점 키워드 도출
        group_keywords = []
        if disease_kcd:
            try:
                rules_res = self.db.table("disease_group_code_rules").select("*").execute()
                matched_group_ids = []
                excluded_group_ids = []
                for rule in rules_res.data or []:
                    start = rule.get("code_start")
                    end = rule.get("code_end")
                    group_id = rule.get("group_id")
                    
                    # KCD 범위 매칭 체크
                    in_range = False
                    kcd_clean = disease_kcd[:3]
                    if start:
                        if end:
                            if start <= kcd_clean <= end:
                                in_range = True
                        else:
                            if disease_kcd.startswith(start):
                                in_range = True
                                
                    if in_range:
                        if rule.get("rule_type") == "include":
                            matched_group_ids.append(group_id)
                        elif rule.get("rule_type") == "exclude":
                            excluded_group_ids.append(group_id)
                
                # 최종 매치 그룹
                final_group_ids = [gid for gid in matched_group_ids if gid not in excluded_group_ids]
                
                if final_group_ids:
                    # disease_groups에서 한글 명칭/라벨 가져오기
                    groups_res = self.db.table("disease_groups").select("id, name, user_label").in_("id", final_group_ids).execute()
                    for group in groups_res.data or []:
                        if group.get("name"):
                            group_keywords.append(group["name"])
                        if group.get("user_label"):
                            group_keywords.append(group["user_label"])
                    
                group_keywords = list(set(group_keywords))
                print(f"[Retriever] Dynamic group keywords for KCD {disease_kcd}: {group_keywords}")
            except Exception as e:
                print(f"[Retriever] Failed to extract dynamic group keywords: {e}")

        # 2. DB에서 전체 chunk 목록 로드 (Mock/Real)
        # 1주차 pnpm workspace 개발 시, full join 또는 riders 로드가 필요하므로
        # select("*, riders(*)") 수행
        try:
            response = self.db.table("rider_chunks").select("*, riders(*)").execute()
            chunks = response.data or []
        except Exception as e:
            print(f"[Retriever] DB select failed: {e}")
            chunks = []

        # 3. 파이썬 레벨 필터링 및 점수 계산
        scored_chunks = []
        # 질의어 형태소 분해 (단순 공백 및 특수문자 제거)
        clean_query = query.replace(",", " ").replace(".", " ")
        query_words = [w for w in clean_query.split() if len(w) >= 2]

        for chunk in chunks:
            meta = chunk.get("meta") or {}
            if isinstance(meta, str):
                import json

                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            # policy_ids 필터 적용 (있는 경우에만)
            if policy_ids and meta.get("policy_id") not in policy_ids:
                continue

            # trigger_type 필터 적용 (있는 경우에만)
            if trigger_type and meta.get("trigger_type") != trigger_type:
                continue

            # 유사도 점수 계산
            sim_score = 0.0

            # 코사인 유사도 (벡터 임베딩이 존재하는 경우)
            if chunk.get("embedding") and q_emb:
                try:
                    v1 = np.array(chunk["embedding"], dtype=np.float32)
                    v2 = np.array(q_emb, dtype=np.float32)
                    norm_v1 = np.linalg.norm(v1)
                    norm_v2 = np.linalg.norm(v2)
                    if norm_v1 > 0 and norm_v2 > 0:
                        sim_score = float(np.dot(v1, v2) / (norm_v1 * norm_v2))
                except Exception:
                    sim_score = 0.0

            # 키워드 매칭 가산점 (환각 방지 및 키워드 기반 매칭 정확도 보장)
            content = chunk.get("content", "")
            rider_obj = chunk.get("riders") or {}
            rider_name = rider_obj.get("name", "")
            keyword_score = 0.0

            # 실손 특약 전용 검색 보정 가산점 (상해/질병 분류 적용)
            is_silsil = "실손" in rider_name
            is_injury_query = any(w in query for w in ["상해", "골절", "사고", "다침"])
            is_disease_query = any(
                w in query
                for w in [
                    "뇌경색",
                    "디스크",
                    "암",
                    "비염",
                    "질병",
                    "질환",
                    "아픔",
                    "위암",
                    "뇌출혈",
                    "뇌혈관",
                ]
            )

            if is_silsil:
                # 상해 상황인데 질병 실손이거나, 질병 상황인데 상해 실손이면 가산점 배제
                if is_injury_query and "질병" in rider_name:
                    keyword_score -= 1.0
                elif is_disease_query and "상해" in rider_name:
                    keyword_score -= 1.0
                else:
                    # 상해/질병 상황별 실손 가산점 보강
                    if is_injury_query and "상해" in rider_name:
                        keyword_score += 1.5
                    elif is_disease_query and "질병" in rider_name:
                        keyword_score += 1.5

                    has_hosp = any(w in query for w in ["입원", "치료"])
                    has_outpatient = any(w in query for w in ["통원", "치료", "외래"])
                    if "입원" in rider_name and has_hosp:
                        keyword_score += 1.2
                    elif "통원" in rider_name and has_outpatient:
                        keyword_score += 1.2
                    else:
                        keyword_score += 0.4

            # 동적 질병 그룹 가산점 (DB 룰 연동 적용)
            dynamic_match_count = 0
            rider_name_clean = clean_for_match(rider_name)
            for gk in group_keywords:
                gk_clean = clean_for_match(gk)
                if gk_clean in rider_name_clean:
                    keyword_score += 1.2 + (len(gk_clean) * 0.2)
                    dynamic_match_count += 1
                elif gk in content:
                    keyword_score += 0.6
                    dynamic_match_count += 1

            # 질병 관련 특약 가산점 (질병 상황 시 일반 질병 특약 매칭 보정)
            is_disease_rider = "질병" in rider_name
            if is_disease_query and is_disease_rider:
                if not is_silsil:
                    keyword_score += 1.5

            # 특정 "진단비" 메인 특약 가산점 (질환 진단 쿼리 시 진단비/진단자금 특약 보정)
            if is_disease_query and any(clean_for_match(w) in rider_name_clean for w in ["진단비", "진단자금", "진단금", "진단"]):
                keyword_score += 0.5

            # 일반 암진단비 / 일반 3대질병진단비 보정 가산점 (특정 부위/한정 암 제외)
            has_cancer = "암" in rider_name_clean
            has_diag_word = any(clean_for_match(w) in rider_name_clean for w in ["진단비", "진단자금", "진단금", "진단"])
            if has_cancer and has_diag_word and not any(
                clean_for_match(w) in rider_name_clean
                for w in [
                    "소아",
                    "남성",
                    "여성",
                    "고액",
                    "특정",
                    "유방",
                    "대장",
                    "자궁",
                    "전립선",
                    "식도",
                ]
            ):
                keyword_score += 0.4

            # 특정 신체부위/질환 한정 특약에 대한 키워드 페널티 (일반 암진단비 누락 방지)
            for limit_kw in [
                "갑상선",
                "소아",
                "남성",
                "여성",
                "고액",
                "특정암",
                "유방암",
                "대장암",
                "자궁",
                "전립선",
                "11대",
                "유사암진단",
                "유사암수술",
            ]:
                limit_kw_clean = clean_for_match(limit_kw)
                if limit_kw_clean in rider_name_clean or limit_kw in content:
                    if limit_kw_clean not in clean_for_match(query):
                        keyword_score -= 0.8

            for word in query_words:
                word_clean = clean_for_match(word)
                if word_clean in rider_name_clean:
                    keyword_score += 1.5  # rider_name에 직접 쿼리 단어가 매칭되는 경우 강력 추천
                elif word in content:
                    keyword_score += 0.1
                    # 핵심 도메인 키워드 추가 가중치
                    if word in [
                        "디스크",
                        "허리디스크",
                        "뇌경색",
                        "뇌졸중",
                        "암",
                        "입원",
                        "수술",
                        "통원",
                    ]:
                        keyword_score += 0.2

            total_score = sim_score + keyword_score
            scored_chunks.append((chunk, total_score))

        # 점수 내림차순 정렬
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # 특약 이름(rider_name) 및 보험(policy_id) 기준 중복 제거
        # (다양한 특약이 노출될 수 있도록 보장)
        unique_rider_chunks = []
        seen_riders = set()
        for chunk, score in scored_chunks:
            rider_obj = chunk.get("riders") or {}
            rider_name = rider_obj.get("name")
            policy_id = rider_obj.get("policy_id")

            # (policy_id, rider_name) 쌍으로 중복을 방지하여 보험사별로 동일 특약은 1개만 남김
            rider_key = (policy_id, rider_name) if rider_name else chunk.get("id")

            if rider_key not in seen_riders:
                seen_riders.add(rider_key)
                unique_rider_chunks.append((chunk, score))

        # 최종 상위 k개 반환
        return [item[0] for item in unique_rider_chunks[: max(k, 80)]]
