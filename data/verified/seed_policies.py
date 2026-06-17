"""
seed_policies.py
6개 검수 완료 약관 JSON → Supabase policies · riders 적재 스크립트

폴더 구조:
  data/verified/
    seed_policies.py          ← 이 파일
    현대해상_실손_손보_실손_검증완료.json
    db손보험_계속받는3대질병_손보_질병_검증완료.json
    kb손보험_9회주는암보험Plus_손보_암_검증완료.json
    메리츠화재_상해안심보험_손보_상해_검증완료.json
    교보생명_NewNew내생애맞춤건강_생보_질병_검증완료.json
    한화생명_e암보험비갱신형_생보_암_검증완료.json

사용법:
  1. pip install -r backend/requirements.txt
  2. 프로젝트 루트에 .env 파일 만들고 아래 두 줄 입력:
       SUPABASE_URL=https://xxxx.supabase.co
       SUPABASE_KEY=여기에_service_role_key
       (service_role key: Supabase 대시보드 → Settings → API → service_role)
  3. 터미널에서: python data/verified/seed_policies.py
"""

import json
import os
from pathlib import Path
from typing import Any, cast
from dotenv import load_dotenv
from supabase import create_client, Client

# .env는 프로젝트 루트(이 파일 기준 3단계 위)에 있다고 가정
# 위치가 다르면 load_dotenv() 경로를 수정하세요
load_dotenv(Path(__file__).parent.parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        ".env 파일에 SUPABASE_URL과 SUPABASE_KEY를 입력해주세요.\n"
        "SUPABASE_KEY는 anon key가 아니라 service_role key여야 합니다.\n"
        "(Supabase 대시보드 → Settings → API → service_role)"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# 적재할 6개 약관 — 이미지 파일명 기준
# 파일명이 조금 다르면 file 항목만 수정하세요
# ============================================================
BASE_DIR = Path(__file__).parent  # data/verified/

POLICY_FILES = [
    {
        "file": "현대해상_실손_손보_실손_검증완료.json",
        "name": "현대해상 Hi실손의료비보험",
        "insurer": "현대해상",
        "type": "실손",
    },
    {
        "file": "db손해보험_계속받는3대질병_손보_질병_검증완료.json",
        "name": "DB 계속받는 3대질병보험",
        "insurer": "DB손해보험",
        "type": "질병",
    },
    {
        "file": "kb손해보험_9회주는암보험Plus_손보_암_검증완료.json",
        "name": "KB 9회주는 암보험Plus",
        "insurer": "KB손해보험",
        "type": "암",
    },
    {
        "file": "메리츠화재_상해안심보험_손보_상해_검증완료.json",
        "name": "메리츠 상해안심보험",
        "insurer": "메리츠화재",
        "type": "상해",
    },
    {
        "file": "교보생명_New내생애맞춤건강_생보_질병_검증완료.json",
        "name": "교보생명 New내생애맞춤건강보험",
        "insurer": "교보생명",
        "type": "질병",
    },
    {
        "file": "한화생명_e암보험비갱신형_생보_암_검증완료.json",
        "name": "한화생명 e암보험(비갱신형)",
        "insurer": "한화생명",
        "type": "암",
    },
]


def insert_policy(meta: dict[str, str]) -> str | None:
    """policies 테이블에 상품 삽입 후 uuid 반환. 이미 있으면 기존 id 반환."""
    existing = (
        supabase.table("policies")
        .select("id")
        .eq("name", meta["name"])
        .execute()
    )

    existing_rows = cast(list[dict[str, Any]], existing.data or [])

    if existing_rows:
        pid = str(existing_rows[0]["id"])
        print(f"  ⏭  이미 존재: {meta['name']} (id={pid[:8]}...)")
        return pid

    res = supabase.table("policies").insert({
        "name": meta["name"],
        "insurer": meta["insurer"],
        "type": meta["type"],
        "is_preset": True,
    }).execute()

    inserted_rows = cast(list[dict[str, Any]], res.data or [])

    if not inserted_rows:
        print(f" policies 삽입 실패: {meta['name']}")
        return None

    pid = str(inserted_rows[0]["id"])
    print(f" policies 삽입: {meta['name']} (id={pid[:8]}...)")
    return pid

def build_rider_row(policy_id: str, r: dict) -> dict:
    """JSON rider 객체 → riders 테이블 row 변환"""
    source = r.get("source") or {}
    return {
        "policy_id":           policy_id,
        "name":                r.get("name"),
        "is_main":             r.get("is_main", False),
        "trigger_type":        r.get("trigger_type"),
        "trigger_detail":      r.get("trigger_detail"),
        "unit_amount":         r.get("unit_amount"),
        "unit_type":           r.get("unit_type"),
        "unit_basis":          r.get("unit_basis"),
        "boundaries": r.get("boundaries") or [],
        "exclusions": r.get("exclusions") or [],
        "limits": r.get("limits") or [],
        "waiting_period_days": r.get("waiting_period_days"),
        "reductions": r.get("reductions") or [],
        "deduct_days":         r.get("deduct_days", 0),
        "article_no":          source.get("article"),
        "page":                source.get("page"),
        "raw_text":            source.get("raw_text"),
        "source_pages": r.get("source_pages") or [],
        "verified":            r.get("verified", False),
        "coverage_kind":       r.get("coverage_kind", "정액"),
        "claim_rule": r.get("claim_rule") or None,
    }


def insert_riders(policy_id: str, riders: list) -> int:
    """riders 배열을 100개씩 배치 삽입. 이미 있으면 건너뜀."""
    existing = (
        supabase.table("riders")
        .select("id")
        .eq("policy_id", policy_id)
        .limit(1)
        .execute()
    )

    existing_rows = cast(list[dict[str, Any]], existing.data or [])

    if existing_rows:
        print("  ⏭  riders 이미 존재 — 건너뜀")
        return 0

    rows = [build_rider_row(policy_id, r) for r in riders]
    total = 0

    for i in range(0, len(rows), 100):
        supabase.table("riders").insert(rows[i:i + 100]).execute()
        total += len(rows[i:i + 100])

    print(f" riders 삽입: {total}건")
    return total


def main():
    print("\n===== 약관 데이터 적재 시작 =====\n")
    total_riders = 0

    for meta in POLICY_FILES:
        file_path = BASE_DIR / meta["file"]
        print(f"[{meta['name']}]")

        if not file_path.exists():
            print(f" 파일 없음: {file_path}")
            print(f"     → 파일명을 확인하고 POLICY_FILES의 file 항목을 수정하세요\n")
            continue

        data = json.loads(file_path.read_text(encoding="utf-8"))
        riders = data.get("riders", [])
        print(f" JSON 로드: riders {len(riders)}건")

        policy_id = insert_policy(meta)
        if policy_id:
            cnt = insert_riders(policy_id, riders)
            total_riders += cnt
        print()

    print(f"===== 완료: 총 riders {total_riders}건 적재 =====")


if __name__ == "__main__":
    main()
