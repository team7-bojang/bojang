"""GET/PATCH /cases/{case_id}/dashboard 계약 테스트 (API 명세서 v2.6 4-12/4-13)."""

import datetime as dt

import jwt

from app.config import settings
from app.db import get_client

OWNER_ID = "00000000-0000-0000-0000-000000000000"  # require_auth 디버그 폴백 사용자
_OTHER_USER_JWT_SECRET = "dashboard-test-secret"  # noqa: S105 - 테스트 전용 더미 시크릿


def _other_user_auth_header(monkeypatch) -> dict:
    """실제 JWT 검증(_verify_supabase_jwt)을 통과하는, 소유자가 다른 사용자의 토큰."""
    monkeypatch.setattr(settings, "supabase_jwt_secret", _OTHER_USER_JWT_SECRET)
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "aud": settings.supabase_jwt_audience,
        "exp": now + dt.timedelta(hours=1),
        "iat": now,
    }
    if settings.supabase_url:
        payload["iss"] = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    token = jwt.encode(payload, _OTHER_USER_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def _create_case(**overrides) -> str:
    db = get_client()
    case = {
        "user_id": OWNER_ID,
        "service_type": "CASE1",
        "disease_name": "허리디스크",
        "disease_kcd": "M511",
        "is_outpatient": True,
        "is_inpatient": False,
        "treatment_items": ["MANUAL_THERAPY"],
        "payment_amount": 90000,
        "visit_dates": ["2026-06-10"],
        "surgery": False,
        "annual_visit_count": 5,
        "policy_elapsed_days": 730,
        **overrides,
    }
    res = db.table("cases").insert(case).execute()
    data = res.data
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("id")
    elif isinstance(data, dict):
        return data.get("id")
    return None


def test_get_dashboard_returns_nine_items(client):
    case_id = _create_case()

    res = client.get(f"/api/v1/cases/{case_id}/dashboard")

    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["case_id"] == case_id
    assert body["data"]["service_type"] == "CASE1"
    dashboard = body["data"]["dashboard"]
    assert dashboard["disease_name"] == "허리디스크"
    assert dashboard["is_outpatient"] is True
    assert dashboard["admission_days_current"] is None
    assert dashboard["treatment_items"] == ["MANUAL_THERAPY"]


def test_get_dashboard_404_when_case_missing(client):
    res = client.get("/api/v1/cases/00000000-0000-0000-0000-111111111111/dashboard")

    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "not_found"


def test_get_dashboard_403_for_other_users_case(client, monkeypatch):
    case_id = _create_case()

    res = client.get(f"/api/v1/cases/{case_id}/dashboard", headers=_other_user_auth_header(monkeypatch))

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "forbidden"


def test_patch_dashboard_updates_only_sent_fields(client):
    case_id = _create_case(annual_visit_count=5)

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"disease_name": "요추 염좌", "annual_visit_count": 2},
    )

    assert res.status_code == 200
    dashboard = res.get_json()["data"]["dashboard"]
    assert dashboard["disease_name"] == "요추 염좌"
    assert dashboard["annual_visit_count"] == 2
    assert dashboard["disease_kcd"] == "M511"  # 보내지 않은 필드는 유지


def test_patch_dashboard_allows_explicit_null(client):
    case_id = _create_case(admission_days_current=7)

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"admission_days_current": None},
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["dashboard"]["admission_days_current"] is None


def test_patch_dashboard_rejects_inpatient_and_outpatient_together(client):
    case_id = _create_case()

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"is_inpatient": True, "is_outpatient": True},
    )

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"


def test_patch_dashboard_rejects_unknown_treatment_code(client):
    case_id = _create_case()

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"treatment_items": ["UNKNOWN_TREATMENT"]},
    )

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"


def test_patch_dashboard_rejects_invalid_visit_date(client):
    case_id = _create_case()

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"visit_dates": ["2026-99-99"]},
    )

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"


def test_patch_dashboard_403_for_other_users_case(client, monkeypatch):
    case_id = _create_case()

    res = client.patch(
        f"/api/v1/cases/{case_id}/dashboard",
        json={"annual_visit_count": 1},
        headers=_other_user_auth_header(monkeypatch),
    )

    assert res.status_code == 403


def test_unknown_route_preserves_404(client):
    res = client.get("/api/v1/does-not-exist")

    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "not_found"
