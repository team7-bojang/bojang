import numpy as np

from app.db import get_client
from app.rag.embedder import embed


class Retriever:
    def __init__(self):
        # get_client()를 통해 Real/Mock Supabase 연동
        self.db = get_client()

    def search(
        self, query: str, policy_ids: list[str] = None, trigger_type: str = None, k: int = 5
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
                    keyword_score -= 10.0
                elif is_disease_query and "상해" in rider_name:
                    keyword_score -= 10.0
                else:
                    has_hosp = any(w in query for w in ["입원", "치료"])
                    has_outpatient = any(w in query for w in ["통원", "치료", "외래"])
                    if "입원" in rider_name and has_hosp:
                        keyword_score += 12.0
                    elif "통원" in rider_name and has_outpatient:
                        keyword_score += 12.0
                    else:
                        keyword_score += 4.0

            # 질병 도메인별 그룹 가산점
            # 뇌혈관질환 그룹
            brain_keywords = [
                "뇌경색",
                "뇌졸중",
                "뇌출혈",
                "뇌혈관",
                "i60",
                "i61",
                "i62",
                "i63",
                "i64",
                "i65",
                "i66",
                "i67",
                "i68",
                "i69",
            ]
            has_brain_query = any(w in query.lower() for w in brain_keywords)
            has_brain_rider = any(
                w in rider_name or w in content for w in ["뇌혈관", "뇌졸중", "뇌출혈"]
            )
            if has_brain_query and has_brain_rider:
                keyword_score += 15.0

            # 암 그룹
            cancer_keywords = [
                "위암",
                "폐암",
                "간암",
                "유방암",
                "대장암",
                "갑상선암",
                "암",
                "악성신생물",
            ]
            has_cancer_query = any(w in query.lower() for w in cancer_keywords)
            has_cancer_rider = any(w in rider_name or w in content for w in ["암", "악성신생물"])
            if has_cancer_query and has_cancer_rider:
                keyword_score += 15.0

            # 척추/디스크 그룹
            spine_keywords = ["디스크", "추간판", "척추", "허리디스크", "m50", "m51"]
            has_spine_query = any(w in query.lower() for w in spine_keywords)
            has_spine_rider = any(
                w in rider_name or w in content for w in ["디스크", "추간판", "척추"]
            )
            if has_spine_query and has_spine_rider:
                keyword_score += 15.0

            # 질병 관련 특약 가산점 (질병 상황 시 일반 질병 특약 매칭 보정)
            is_disease_rider = "질병" in rider_name
            if is_disease_query and is_disease_rider:
                if not is_silsil:
                    keyword_score += 15.0

            # 특정 "진단비" 메인 특약 가산점 (질환 진단 쿼리 시 진단비/진단자금 특약 보정)
            if is_disease_query and any(w in rider_name for w in ["진단비", "진단자금", "진단금"]):
                keyword_score += 5.0

            # 일반 암진단비 / 일반 3대질병진단비 보정 가산점 (특정 부위/한정 암 제외)
            if any(w in rider_name for w in ["암진단비", "암진단자금"]) and not any(
                w in rider_name
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
                keyword_score += 4.0

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
                if limit_kw in rider_name or limit_kw in content:
                    if limit_kw not in query:
                        keyword_score -= 8.0

            for word in query_words:
                if word in content or word in rider_name:
                    keyword_score += 0.5
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
                        keyword_score += 2.0

            total_score = sim_score + keyword_score
            scored_chunks.append((chunk, total_score))

        # 점수 내림차순 정렬
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # 특약 이름(rider_name) 및 보험(policy_id) 기준 중복 제거
        # (다양한 특약이 노출될 수 있도록 보장)
        unique_rider_chunks = []
        seen_riders = set()
        policy_trigger_counts = {}  # (policy_id, trigger_type) 별 노출 개수 카운트
        for chunk, score in scored_chunks:
            rider_obj = chunk.get("riders") or {}
            rider_name = rider_obj.get("name")
            policy_id = rider_obj.get("policy_id")
            trigger_type = rider_obj.get("trigger_type") or "기타"

            # (policy_id, rider_name) 쌍으로 중복을 방지하여 보험사별로 동일 특약은 1개만 남김
            rider_key = (policy_id, rider_name) if rider_name else chunk.get("id")

            if rider_key not in seen_riders:
                # 보험사별 + 담보유형(진단/입원/수술)별 최대 노출 개수 제한 (다양성 극대화)
                if policy_id:
                    trigger_key = (policy_id, trigger_type)
                    current_count = policy_trigger_counts.get(trigger_key, 0)

                    # 진단/입원/수술 각각 최대 4개씩만 허용 (나머지 기타는 최대 2개)
                    max_allowed = 4 if trigger_type in ["진단", "입원", "수술"] else 2
                    if current_count >= max_allowed:
                        continue  # 해당 담보 유형은 이미 충분히 노출되었으므로 스킵
                    policy_trigger_counts[trigger_key] = current_count + 1

                seen_riders.add(rider_key)
                unique_rider_chunks.append((chunk, score))

        # 최종 상위 k개 반환
        return [item[0] for item in unique_rider_chunks[: max(k, 25)]]
