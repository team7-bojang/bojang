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


def test_upload_pdf_copies_pages_from_other_users_existing_policy(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "44444444-4444-4444-4444-444444444444"
    db_instance.policies.append(
        {
            "id": source_policy_id,
            "name": "원본 사용자 약관",
            "insurer": "직접업로드",
            "type": "질병",
            "is_preset": False,
            "user_id": OWNER_ID,
            "pdf_hash": pdf_hash,
        }
    )
    db_instance.policy_pages.extend(
        {"policy_id": source_policy_id, "page_num": p["page_num"], "text": p["text"]} for p in _pages()
    )

    def fail_extract(pdf_bytes):
        raise AssertionError("다른 사용자가 이미 추출해둔 PDF면 pdfplumber를 다시 돌리면 안 됩니다.")

    monkeypatch.setattr(user_policy_service, "extract_pages", fail_extract)

    result = user_policy_service.upload_pdf(OTHER_USER_ID, "same.pdf", PDF_BYTES)

    assert result["policy_id"] != source_policy_id
    assert result["page_count"] == 2
    copied = [p for p in db_instance.policy_pages if p["policy_id"] == result["policy_id"]]
    assert sorted(p["page_num"] for p in copied) == [1, 2]
    assert {p["text"] for p in copied} == {p["text"] for p in _pages()}


def test_get_or_parse_riders_falls_back_to_llm_when_shared_cache_is_stale(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "55555555-5555-5555-5555-555555555555"
    target_policy_id = "66666666-6666-6666-6666-666666666666"
    q_hash = user_policy_service._make_query_hash(pdf_hash, "K29", "위염", [])

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
    # source 쪽에 캐시 행만 있고 riders는 아직 없음 — 동시 진행 중인 파싱(레이스)을 흉내냄
    db_instance.policy_parse_cache.append(
        {"id": "cache-source-stale", "policy_id": source_policy_id, "query_hash": q_hash, "content_key": pdf_hash}
    )
    db_instance.policy_pages.extend(
        {"policy_id": target_policy_id, "page_num": p["page_num"], "text": p["text"]} for p in _pages()
    )

    calls = {"llm": 0}

    def fake_parse(pages, context=""):
        calls["llm"] += 1
        return [{"name": "위염 통원 특약", "trigger_type": "통원", "unit_type": "1회당"}]

    monkeypatch.setattr(user_policy_service, "_parse_pages_with_llm", fake_parse)
    monkeypatch.setattr(user_policy_service, "embed", lambda texts: [[0.0] * 3 for _ in texts])

    result = user_policy_service.get_or_parse_riders(OTHER_USER_ID, target_policy_id, "K29", "위염", [])

    assert calls["llm"] == 1
    assert len(result) == 1
    assert result[0]["policy_id"] == target_policy_id
    assert any(
        row["policy_id"] == target_policy_id and row["query_hash"] == q_hash for row in db_instance.policy_parse_cache
    )


def test_get_or_parse_riders_rolls_back_on_clone_failure(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "77777777-7777-7777-7777-777777777777"
    target_policy_id = "88888888-8888-8888-8888-888888888888"
    q_hash = user_policy_service._make_query_hash(pdf_hash, "M51", "디스크", [])

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
        {"id": "cache-source", "policy_id": source_policy_id, "query_hash": q_hash, "content_key": pdf_hash}
    )

    def boom_clone(source_policy_id, target_policy_id, query_hash):
        raise RuntimeError("시뮬레이션된 클론 실패")

    monkeypatch.setattr(user_policy_service, "_clone_riders", boom_clone)

    with pytest.raises(RuntimeError, match="시뮬레이션된 클론 실패"):
        user_policy_service.get_or_parse_riders(OTHER_USER_ID, target_policy_id, "M51", "디스크", [])

    assert not [
        row
        for row in db_instance.policy_parse_cache
        if row["policy_id"] == target_policy_id and row["query_hash"] == q_hash
    ]
    assert not [r for r in db_instance.riders if r["policy_id"] == target_policy_id and r["parse_query_hash"] == q_hash]


def test_get_or_parse_riders_returns_existing_on_duplicate_lock_race(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "99999999-9999-9999-9999-999999999999"
    target_policy_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    q_hash = user_policy_service._make_query_hash(pdf_hash, "S82", "골절", [])

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
        {"id": "cache-source", "policy_id": source_policy_id, "query_hash": q_hash, "content_key": pdf_hash}
    )
    # "동시 요청"이 이미 완료해 target에 저장해둔 결과
    winning_rider = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "policy_id": target_policy_id,
        "parse_query_hash": q_hash,
        "name": "골절 진단 특약",
        "is_main": False,
        "trigger_type": "골절",
        "trigger_detail": "골절 진단 시 보장",
        "unit_amount": 200000,
        "unit_type": "1회당",
        "unit_basis": "1회당 20만원",
        "boundaries": [],
        "exclusions": [],
        "limits": [],
        "waiting_period_days": None,
        "reductions": [],
        "deduct_days": 0,
        "claim_rule": None,
        "source_pages": [1],
        "article_no": "제2조",
        "page": 1,
        "raw_text": "골절 진단 시 보장",
        "verified": False,
        "coverage_kind": "정액",
    }
    db_instance.riders.append(winning_rider)

    from app.db import mock_db as mock_db_module

    original_execute = mock_db_module.MockQueryBuilder.execute
    state = {"triggered": False}

    def patched_execute(self):
        if (
            not state["triggered"]
            and self.table_name == "policy_parse_cache"
            and self._is_insert
            and isinstance(self._mutation_data, dict)
            and self._mutation_data.get("policy_id") == target_policy_id
        ):
            state["triggered"] = True
            raise ValueError("duplicate key value violates unique constraint")
        return original_execute(self)

    monkeypatch.setattr(mock_db_module.MockQueryBuilder, "execute", patched_execute)

    def fail_clone(*args, **kwargs):
        raise AssertionError("동시 락 충돌 시 다시 복제하면 안 되고 기존 결과를 재조회해야 합니다.")

    monkeypatch.setattr(user_policy_service, "_clone_riders", fail_clone)

    result = user_policy_service.get_or_parse_riders(OTHER_USER_ID, target_policy_id, "S82", "골절", [])

    assert state["triggered"] is True
    assert len(result) == 1
    assert result[0]["id"] == winning_rider["id"]


def test_clone_riders_recomputes_embedding_when_missing(monkeypatch):
    pdf_hash = user_policy_service.hashlib.sha256(PDF_BYTES).hexdigest()
    source_policy_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    target_policy_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    q_hash = user_policy_service._make_query_hash(pdf_hash, "K29", "위염", [])

    rider = {
        "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        "policy_id": source_policy_id,
        "parse_query_hash": q_hash,
        "name": "위염 통원 특약",
        "is_main": False,
        "trigger_type": "통원",
        "trigger_detail": "위염 통원 치료 시 보장",
        "unit_amount": 50000,
        "unit_type": "1회당",
        "unit_basis": "1회당 5만원",
        "boundaries": [],
        "exclusions": [],
        "limits": [],
        "waiting_period_days": None,
        "reductions": [],
        "deduct_days": 0,
        "claim_rule": None,
        "source_pages": [1],
        "article_no": "제3조",
        "page": 1,
        "raw_text": "위염 통원 치료 시 보장",
        "verified": False,
        "coverage_kind": "정액",
    }
    db_instance.riders.append(rider)
    # source 쪽 rider_chunks 를 일부러 비워둠 — 캐시된 임베딩이 없는 상태를 흉내냄

    calls = {"embed": 0}

    def fake_embed(texts):
        calls["embed"] += 1
        return [[0.0] * 3 for _ in texts]

    monkeypatch.setattr(user_policy_service, "embed", fake_embed)

    cloned = user_policy_service._clone_riders(source_policy_id, target_policy_id, q_hash)

    assert len(cloned) == 1
    assert calls["embed"] >= 1
    new_chunks = [c for c in db_instance.rider_chunks if c["rider_id"] == cloned[0]["id"]]
    assert new_chunks
    assert all(c["embedding"] == [0.0, 0.0, 0.0] for c in new_chunks)
