"""require_auth JWT 검증 계약 테스트.

Supabase access token(HS256) 서명·만료·audience 검증을 고정한다.
순수 검증 로직은 _verify_supabase_jwt 로, 데코레이터 동작은 라우트 통합으로 확인한다.
"""

import datetime as dt

import jwt
import pytest
from flask import Flask, g, jsonify

from app.auth.middleware import require_auth
from app.config import settings
from app.core.errors import AuthError

SECRET = "test-secret"
USER_ID = "11111111-1111-1111-1111-111111111111"
SUPABASE_URL = "https://proj.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"


def _make_token(secret=SECRET, *, aud="authenticated", iss=ISSUER, sub=USER_ID, expired=False, alg="HS256"):
    now = dt.datetime.now(dt.UTC)
    exp = now - dt.timedelta(hours=1) if expired else now + dt.timedelta(hours=1)
    payload = {"sub": sub, "aud": aud, "iss": iss, "exp": exp, "iat": now}
    return jwt.encode(payload, secret, algorithm=alg)


@pytest.fixture
def auth_env(monkeypatch):
    """검증을 켠 상태(secret 설정, debug 폴백 무력화 가능)로 고정."""
    monkeypatch.setattr(settings, "supabase_jwt_secret", SECRET)
    monkeypatch.setattr(settings, "supabase_jwt_audience", "authenticated")
    monkeypatch.setattr(settings, "supabase_url", SUPABASE_URL)
    return settings


@pytest.fixture
def app(auth_env):
    app = Flask(__name__)

    @app.route("/protected")
    @require_auth
    def protected():
        return jsonify(user_id=g.user_id)

    @app.errorhandler(AuthError)
    def _handle(e):
        return jsonify(error=e.message), e.http_status

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_valid_token_injects_user_id(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_token()))
    assert res.status_code == 200
    assert res.get_json()["user_id"] == USER_ID


def test_wrong_signature_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_token(secret="attacker-secret")))
    assert res.status_code == 401


def test_expired_token_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_token(expired=True)))
    assert res.status_code == 401


def test_wrong_audience_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_token(aud="anon")))
    assert res.status_code == 401


def test_wrong_issuer_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_token(iss="https://evil.supabase.co/auth/v1")))
    assert res.status_code == 401


def test_missing_header_rejected_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected")
    assert res.status_code == 401


def test_debug_fallback_allows_test_token(client, monkeypatch):
    monkeypatch.setattr(settings, "debug", True)
    res = client.get("/protected", headers=_auth("test-token"))
    assert res.status_code == 200
    assert res.get_json()["user_id"] == "00000000-0000-0000-0000-000000000000"


def test_debug_does_not_bypass_real_token(client, monkeypatch):
    """debug 라도 진짜 형식의 토큰은 검증한다(폴백은 더미 토큰 한정)."""
    monkeypatch.setattr(settings, "debug", True)
    res = client.get("/protected", headers=_auth(_make_token(secret="attacker-secret")))
    assert res.status_code == 401


def test_real_app_maps_auth_error_to_401_envelope(monkeypatch):
    """실제 create_app 에서 AuthError 가 500 이 아닌 401 응답 봉투로 변환되는지 고정.

    (AppError 핸들러 누락 회귀 방지 — 누락 시 500 HTML 이 새어 나갔다.)
    """
    from app.factory import create_app

    monkeypatch.setattr(settings, "debug", False)
    real_client = create_app().test_client()

    res = real_client.get("/api/v1/policies/my")  # 토큰 없는 보호 라우트
    assert res.status_code == 401
    body = res.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == "unauthorized"
