import pytest

from app.db.mock_db import db_instance
from app.rag.chunker import chunk_rider
from app.services import user_policy_service

OWNER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "00000000-0000-0000-0000-000000000002"
PDF_BYTES = b"%PDF-1.4 same policy bytes"


@pytest.fixture(autouse=True)
def _reset_policy_cache_tables():
    db_instance.policies = []
    db_instance.policy_pages = []
    db_instance.policy_parse_cache = []
    db_instance.riders = []
    db_instance.rider_chunks = []
    db_instance._initialized = True


def _pages():
    return [
        {
            "page_num": 1,
            "text": "[PAGE 1]\n질병 입원 일당 보장 및 MRI 치료 보장 내용입니다. " * 3,
        },
        {
            "page_num": 2,
            "text": "[PAGE 2]\n질병 수술비 보장 내용입니다. " * 3,
        },
    ]


def test_upload_pdf_reuses_same_users_existing_policy(monkeypatch):
    calls = {"extract": 0}

    def fake_extract_pages(pdf_bytes):
        calls["extract"] += 1
        return _pages()

    monkeypatch.setattr(user_policy_service, "extract_pages", fake_extract_pages)

    first = user_policy_service.upload_pdf(OWNER_ID, "same.pdf", PDF_BYTES)
    second = user_policy_service.upload_pdf(OWNER_ID, "same.pdf", PDF_BYTES)

    assert second == first
    assert calls["extract"] == 1
    assert len(db_instance.policies) == 1
    assert len(db_instance.policy_pages) == 2


def test_upload_pdf_ignores_stale_policy_without_pages(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    db_instance.policies.append(
        {
            "id": "stale-policy",
            "name": "stale",
            "insurer": "직접업로드",
            "type": "질병",
            "is_preset": False,
            "user_id": OWNER_ID,
            "pdf_hash": pdf_hash,
        }
    )
    monkeypatch.setattr(user_policy_service, "extract_pages", lambda pdf_bytes: _pages())

    result = user_policy_service.upload_pdf(OWNER_ID, "same.pdf", PDF_BYTES)

    assert result["policy_id"] != "stale-policy"
    assert result["page_count"] == 2
    assert all(policy["id"] != "stale-policy" for policy in db_instance.policies)


def test_get_or_parse_riders_clones_shared_pdf_cache_without_llm(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "11111111-1111-1111-1111-111111111111"
    target_policy_id = "22222222-2222-2222-2222-222222222222"
    q_hash = user_policy_service._make_query_hash(pdf_hash, "M51", "추간판장애", ["MRI_MRA"])

    db_instance.policies.extend(
        [
            {
                "id": source_policy_id,
                "name": "원본 약관",
                "insurer": "직접업로드",
                "type": "질병",
                "is_preset": False,
                "user_id": OWNER_ID,
                "pdf_hash": pdf_hash,
            },
            {
                "id": target_policy_id,
                "name": "복제 대상 약관",
                "insurer": "직접업로드",
                "type": "질병",
                "is_preset": False,
                "user_id": OTHER_USER_ID,
                "pdf_hash": pdf_hash,
            },
        ]
    )
    db_instance.policy_parse_cache.append(
        {
            "id": "cache-source",
            "policy_id": source_policy_id,
            "query_hash": q_hash,
            "content_key": pdf_hash,
        }
    )
    rider = {
        "id": "33333333-3333-3333-3333-333333333333",
        "policy_id": source_policy_id,
        "parse_query_hash": q_hash,
        "name": "질병 MRI 특약",
        "is_main": False,
        "trigger_type": "치료",
        "trigger_detail": "MRI 치료 시 보장",
        "unit_amount": 100000,
        "unit_type": "1회당",
        "unit_basis": "1회당 10만원",
        "boundaries": [],
        "exclusions": [],
        "limits": [],
        "waiting_period_days": None,
        "reductions": [],
        "deduct_days": 0,
        "claim_rule": None,
        "source_pages": [1],
        "article_no": "제1조",
        "page": 1,
        "raw_text": "MRI 치료 시 보장",
        "verified": False,
        "coverage_kind": "정액",
    }
    db_instance.riders.append(rider)
    for chunk in chunk_rider(rider):
        chunk["embedding"] = [0.1, 0.2, 0.3]
        db_instance.rider_chunks.append(chunk)

    def fail_parse(*args, **kwargs):
        raise AssertionError("공유 캐시가 있으면 LLM 파싱을 호출하지 않아야 합니다.")

    monkeypatch.setattr(user_policy_service, "_parse_pages_with_llm", fail_parse)

    cloned = user_policy_service.get_or_parse_riders(
        OTHER_USER_ID,
        target_policy_id,
        "M51",
        "추간판장애",
        treatment_items=["MRI_MRA"],
    )

    assert len(cloned) == 1
    assert cloned[0]["policy_id"] == target_policy_id
    assert cloned[0]["name"] == "질병 MRI 특약"
    assert any(
        row["policy_id"] == target_policy_id and row["query_hash"] == q_hash for row in db_instance.policy_parse_cache
    )
    assert any(chunk["rider_id"] == cloned[0]["id"] for chunk in db_instance.rider_chunks)
