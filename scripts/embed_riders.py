"""
embed_riders.py
Supabase riders 테이블 → rider_chunks 임베딩 적재 스크립트

동작:
  1. Supabase에서 riders 전체 조회
  2. 각 rider의 내용을 텍스트로 조합 (청킹)
  3. OpenAI text-embedding-3-small로 임베딩 생성
  4. rider_chunks 테이블에 저장

사용법:
  1. .env에 아래 키 추가:
       OPENAI_API_KEY=sk-...
  2. python scripts/embed_riders.py
     또는 프로젝트 루트에서: python embed_riders.py

주의:
  - 이미 chunks가 있는 rider는 건너뜀 (중복 방지)
  - OpenAI API 비용 발생 (text-embedding-3-small: $0.02/1M tokens)
  - 391건 기준 약 $0.01 미만 예상
"""

import json
import os
import time
from typing import Any, cast
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(".env에 SUPABASE_URL, SUPABASE_KEY를 입력해주세요.")
if not OPENAI_API_KEY:
    raise ValueError(".env에 OPENAI_API_KEY를 입력해주세요.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # OpenAI API 배치 크기


def build_chunk_text(rider: dict) -> str:
    """
    rider 필드를 합쳐서 임베딩용 텍스트 생성.
    RAG 검색 시 이 텍스트가 쿼리와 매칭됨.
    """
    parts = []

    # 1. 특약명
    if rider.get("name"):
        parts.append(f"[특약명] {rider['name']}")

    # 2. 지급 사유 유형
    if rider.get("trigger_type"):
        parts.append(f"[지급유형] {rider['trigger_type']}")

    # 3. 지급 조건 상세 (핵심)
    if rider.get("trigger_detail"):
        parts.append(f"[지급조건] {rider['trigger_detail']}")

    # 4. 단가 기준 설명
    if rider.get("unit_basis"):
        parts.append(f"[보장기준] {rider['unit_basis']}")

    # 5. 면책 조항 (제외 조건)
    exclusions = rider.get("exclusions")
    if exclusions:
        if isinstance(exclusions, str):
            exclusions = json.loads(exclusions)
        if exclusions:
            excl_text = " / ".join(str(e) for e in exclusions[:5])  # 최대 5개
            parts.append(f"[면책] {excl_text}")

    # 6. 약관 원문 (검증용)
    if rider.get("raw_text"):
        parts.append(f"[원문] {rider['raw_text']}")

    return "\n".join(parts)


def build_meta(rider: dict) -> dict:
    """rider_chunks.meta 필드용 딕셔너리"""
    return {
        "policy_id":    rider.get("policy_id"),
        "page":         rider.get("page"),
        "article_no":   rider.get("article_no"),
        "trigger_type": rider.get("trigger_type"),
        "coverage_kind": rider.get("coverage_kind", "정액"),
        "verified":     rider.get("verified", False),
    }


def get_existing_rider_ids() -> set[str]:
    """이미 chunks가 있는 rider_id 집합 반환 (중복 방지)"""
    res = supabase.table("rider_chunks").select("rider_id").execute()
    rows = cast(list[dict[str, Any]], res.data or [])
    return {str(row["rider_id"]) for row in rows}


def fetch_all_riders() -> list:
    """riders 테이블 전체 조회 (1000건 이상 대비 페이지네이션)"""
    all_riders = []
    page = 0
    page_size = 500
    while True:
        res = (
            supabase.table("riders")
            .select("*")
            .range(page * page_size, (page + 1) * page_size - 1)
            .execute()
        )
        all_riders.extend(res.data)
        if len(res.data) < page_size:
            break
        page += 1
    return all_riders


def embed_texts(texts: list[str]) -> list[list[float]]:
    """OpenAI API로 텍스트 배치 임베딩. 리스트[벡터] 반환."""
    res = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in res.data]


def main():
    print("\n===== rider_chunks 임베딩 적재 시작 =====\n")

    # 1. 이미 chunks 있는 rider_id 확인
    existing_ids = get_existing_rider_ids()
    print(f"이미 임베딩된 riders: {len(existing_ids)}건\n")

    # 2. 전체 riders 조회
    riders = fetch_all_riders()
    print(f"전체 riders: {len(riders)}건")

    # 3. 미처리 rider만 필터
    todo = [r for r in riders if r["id"] not in existing_ids]
    print(f"임베딩 필요: {len(todo)}건\n")

    if not todo:
        print("모두 임베딩 완료돼 있어요!")
        return

    # 4. 배치 처리
    total = 0
    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"배치 {batch_num}/{total_batches} 처리 중... ({len(batch)}건)")

        # 텍스트 생성
        texts = [build_chunk_text(r) for r in batch]

        # 임베딩 생성
        try:
            vectors = embed_texts(texts)
        except Exception as e:
            print(f" 임베딩 오류: {e}")
            time.sleep(2)
            continue

        # rider_chunks 삽입
        rows = []
        for rider, text, vector in zip(batch, texts, vectors):
            rows.append({
                "rider_id":  rider["id"],
                "content":   text,
                "embedding": vector,
                "meta":      json.dumps(build_meta(rider), ensure_ascii=False),
            })

        supabase.table("rider_chunks").insert(rows).execute()
        total += len(rows)
        print(f" {total}건 완료")

        # API 레이트리밋 방지
        if i + BATCH_SIZE < len(todo):
            time.sleep(0.5)

    print(f"\n===== 완료: 총 {total}건 임베딩 적재 =====")


if __name__ == "__main__":
    main()
