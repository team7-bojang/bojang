"""case 생성과 분석 범위 계약 회귀 테스트."""

import uuid

from app.db import get_client
from app.services import analysis_service, case_service

OWNER_ID = "00000000-0000-0000-0000-000000000000"


def _create_policy(user_id: str = OWNER_ID, name: str = None) -> str:
    policy_name = name or "테스트 보험"
    policy_name = f"{policy_name} {uuid.uuid4()}"
    res = (
        get_client()
        .table("policies")
        .insert(
            {
                "name": policy_name,
                "insurer": "테스트 보험사",
                "type": "질병",
                "is_preset": False,
                "user_id": user_id,
            }
        )
        .execute()
    )
    data = res.data
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("id")
    elif isinstance(data, dict):
        return data.get("id")
    return None


def test_create_case_rejects_other_users_policy(client):
    policy_id = _create_policy("11111111-1111-1111-1111-111111111111")

    res = client.post(
        "/api/v1/cases",
        json={
            "service_type": "CASE1",
            "policy_ids": [policy_id],
            "initial_situation": "허리 통증으로 입원했습니다.",
        },
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "forbidden"


def test_create_case_persists_only_bojang_cases_columns(monkeypatch):
    policy_id = _create_policy()
    monkeypatch.setattr(
        case_service,
        "_classify_intent_llm",
        lambda situation: ("BEFORE_CLAIM", "PAYMENT", "테스트"),
    )

    result = case_service.create_case(
        OWNER_ID,
        "CASE1",
        [policy_id],
        "허리 통증으로 병원에 다녀왔습니다.",
    )
    case = get_client().table("cases").select("*").eq("id", result["case_id"]).execute().data[0]

    assert "initial_situation" not in case
    assert "claim_status" not in case
    assert "recommended_input_method" not in case
    assert case["policy_elapsed_days"] is None


def test_save_answers_endpoint_accepts_disease_selection_json(client, monkeypatch):
    policy_id = _create_policy()
    monkeypatch.setattr(
        case_service,
        "_classify_intent_llm",
        lambda situation: ("BEFORE_CLAIM", "PAYMENT", "테스트"),
    )
    case_id = case_service.create_case(
        OWNER_ID,
        "CASE1",
        [policy_id],
        "허리 아파서 병원 다녀왔어요",
    )["case_id"]

    res = client.post(
        f"/api/v1/cases/{case_id}/answers",
        json={
            "answers": [
                {"question_id": "disease_kcd", "value": "M51"},
                {"question_id": "disease_name", "value": "허리디스크"},
            ]
        },
    )

    assert res.status_code == 200
    case = get_client().table("cases").select("*").eq("id", case_id).execute().data[0]
    assert case["disease_kcd"] == "M51"
    assert case["disease_name"] == "허리디스크"


def test_save_answers_endpoint_returns_403_for_other_users_case(client, monkeypatch):
    policy_id = _create_policy()
    monkeypatch.setattr(
        case_service,
        "_classify_intent_llm",
        lambda situation: ("BEFORE_CLAIM", "PAYMENT", "테스트"),
    )
    case_id = case_service.create_case(
        OWNER_ID,
        "CASE1",
        [policy_id],
        "허리 아파서 병원 다녀왔어요",
    )["case_id"]
    monkeypatch.setattr("app.auth.middleware._verify_supabase_jwt", lambda token: "other-user-id")

    res = client.post(
        f"/api/v1/cases/{case_id}/answers",
        headers={"Authorization": "Bearer real-token"},
        json={"answers": [{"question_id": "disease_kcd", "value": "M51"}]},
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "forbidden"


def test_openapi_documents_answers_request_body(client):
    res = client.get("/openapi/openapi.json")

    assert res.status_code == 200
    operation = res.get_json()["paths"]["/api/v1/cases/{case_id}/answers"]["post"]
    assert "requestBody" in operation


def test_search_analysis_uses_selected_policies_and_new_admission_columns(monkeypatch):
    selected_policy_id = _create_policy(name="선택 보험")
    _create_policy(name="선택하지 않은 보험")
    monkeypatch.setattr(
        case_service,
        "_classify_intent_llm",
        lambda situation: ("BEFORE_CLAIM", "PAYMENT", "테스트"),
    )
    case_id = case_service.create_case(
        OWNER_ID,
        "CASE1",
        [selected_policy_id],
        "허리디스크로 7일 입원했습니다.",
    )["case_id"]

    captured = {}

    def fake_search(self, query, policy_ids=None, trigger_type=None, k=5, **kwargs):
        captured["query"] = query
        captured["policy_ids"] = policy_ids
        return [
            {
                "rider_id": "rider-1",
                "content": "테스트 약관",
                "riders": {
                    "id": "rider-1",
                    "policy_id": selected_policy_id,
                    "name": "입원일당",
                    "trigger_type": "입원",
                    "boundaries": [],
                    "exclusions": [],
                    "limits": [],
                    "reductions": [],
                    "deduct_days": 0,
                    "unit_amount": 10000,
                    "unit_type": "1일당",
                    "claim_rule": None,
                    "source_pages": [],
                    "verified": True,
                },
            }
        ]

    def fake_judge(case, rider):
        captured["judge_case"] = case
        return {"status": "eligible", "gap_days": None, "calc": None}

    monkeypatch.setattr(analysis_service.Retriever, "search", fake_search)
    monkeypatch.setattr(analysis_service, "judge", fake_judge)
    monkeypatch.setattr(
        analysis_service,
        "explain",
        lambda case, judgement, chunks: {
            "explanation": "테스트",
            "article": None,
            "page": None,
            "quote": None,
        },
    )

    result = analysis_service.search_analysis(OWNER_ID, case_id)

    assert len(result["results"]) == 1
    assert captured["policy_ids"] == [selected_policy_id]
    assert "7일 입원" in captured["query"]
    assert captured["judge_case"]["diag_days"] == 7
    assert captured["judge_case"]["current_days"] == 7
