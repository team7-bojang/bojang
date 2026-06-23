"""require_auth JWT 검증 계약 테스트.

Supabase access token(HS256) 서명·만료·audience 검증을 고정한다.
순수 검증 로직은 _verify_supabase_jwt 로, 데코레이터 동작은 라우트 통합으로 확인한다.
"""

import datetime as dt

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from flask import Flask, g, jsonify

import app.auth.middleware as middleware
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


# ── ES256(JWKS 비대칭 키) 검증 ── Supabase 신규 서명 키 기본값.


def _make_es256_token(private_key, *, aud="authenticated", iss=ISSUER, sub=USER_ID, expired=False):
    now = dt.datetime.now(dt.UTC)
    exp = now - dt.timedelta(hours=1) if expired else now + dt.timedelta(hours=1)
    payload = {"sub": sub, "aud": aud, "iss": iss, "exp": exp, "iat": now}
    return jwt.encode(payload, private_key, algorithm="ES256")


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


@pytest.fixture
def es256_keys(monkeypatch):
    """EC P-256 키쌍을 만들고, JWKS 클라이언트가 그 공개키를 반환하도록 패치."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    class _FakeClient:
        def get_signing_key_from_jwt(self, token):
            return _FakeSigningKey(public_key)

    monkeypatch.setattr(middleware, "_get_jwks_client", lambda: _FakeClient())
    return private_key, public_key


def test_es256_token_verified_via_jwks(client, monkeypatch, es256_keys):
    private_key, _ = es256_keys
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_es256_token(private_key)))
    assert res.status_code == 200
    assert res.get_json()["user_id"] == USER_ID


def test_es256_wrong_key_rejected(client, monkeypatch, es256_keys):
    monkeypatch.setattr(settings, "debug", False)
    # 다른 개인키로 서명한 토큰 → JWKS 공개키와 불일치
    attacker_key = ec.generate_private_key(ec.SECP256R1())
    res = client.get("/protected", headers=_auth(_make_es256_token(attacker_key)))
    assert res.status_code == 401


def test_es256_expired_rejected(client, monkeypatch, es256_keys):
    private_key, _ = es256_keys
    monkeypatch.setattr(settings, "debug", False)
    res = client.get("/protected", headers=_auth(_make_es256_token(private_key, expired=True)))
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
