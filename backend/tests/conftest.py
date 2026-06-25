"""pytest 공용 픽스처."""

import os

import pytest

# app.config.settings 는 모듈 임포트 시점에 Settings() 를 생성한다(app/config.py 최하단).
# 로컬 .env 의 DEBUG 값이 "release" 처럼 bool로 파싱 안 되는 값이면 이 생성 자체가
# ValidationError 로 죽어 테스트 수집이 시작도 못 한다. app 모듈 import 전에 pytest_configure에서
# 정상화한다(환경변수가 .env 파일보다 우선이므로 덮어쓰면 막힌다).


def pytest_configure(config):
    debug_value = os.environ.get("DEBUG")
    if debug_value not in {None, "True", "False", "true", "false", "1", "0"}:
        os.environ["DEBUG"] = "True"


@pytest.fixture(autouse=True)
def _isolated_mock_db(monkeypatch):
    """모든 테스트가 .env의 실제 Supabase 대신 격리된 mock DB를 쓰도록 강제한다.

    로컬 .env 에 실제 Supabase 키가 있어도 pytest 실행 중엔 그 DB에 데이터가 쓰이지 않게 하고,
    테스트마다 싱글턴을 리셋해 이전 테스트의 데이터가 다음 테스트로 새지 않게 한다.
    """
    import app.db.client as db_client

    monkeypatch.setenv("MOCK_DB", "True")
    if hasattr(db_client._local, "client"):
        delattr(db_client._local, "client")


@pytest.fixture(autouse=True)
def _debug_auth_fallback(monkeypatch):
    """require_auth 디버그 폴백이 로컬 .env의 DEBUG 값과 무관하게 항상 동작하게 한다.

    헤더 없는 요청만 디버그 사용자로 우회되고, 실제 Bearer 토큰이 있으면 여전히 검증을 거친다
    (app/auth/middleware.py::require_auth 참고).
    """
    from app.config import settings

    monkeypatch.setattr(settings, "debug", True)


@pytest.fixture
def app():
    from app.factory import create_app

    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
