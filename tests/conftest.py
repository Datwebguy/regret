from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["REGRET_ENV"] = "test"
os.environ["REGRET_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["REGRET_ENCRYPTION_KEY"] = "a" * 32
os.environ["REGRET_DATABASE_URL"] = "sqlite:///" + str(Path(__file__).resolve().parent / "test_regret.db").replace("\\", "/")
os.environ["REGRET_LIVE_TRADING_ENABLED"] = "false"
os.environ["ALPACA_OAUTH_CLIENT_ID"] = ""
os.environ["ALPACA_OAUTH_CLIENT_SECRET"] = ""
os.environ["ALPACA_API_KEY"] = ""
os.environ["ALPACA_SECRET_KEY"] = ""
os.environ["ALPACA_DATA_API_KEY_ID"] = ""
os.environ["ALPACA_DATA_API_SECRET_KEY"] = ""
os.environ["FEATHERLESS_API_KEY"] = ""
os.environ["REGRET_LLM_API_KEY"] = ""
os.environ["REGRET_LOGIN_FAIL_LIMIT_EMAIL"] = "1000"
os.environ["REGRET_LOGIN_FAIL_LIMIT_IP"] = "1000"
os.environ["REGRET_REGISTER_LIMIT_IP"] = "1000"

from regret.config import reset_settings_cache
from regret.db.session import get_session_factory, init_db, reset_engine


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path):
    db_path = tmp_path / "regret.db"
    os.environ["REGRET_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    reset_settings_cache()
    reset_engine()
    from regret.services.rate_limit import limiter

    limiter.reset()
    init_db()
    yield
    reset_engine()
    reset_settings_cache()
    limiter.reset()


@pytest.fixture
def db() -> Session:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    from regret.api.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, email: str, password: str = "super-secret-pass") -> dict:
    response = client.post("/api/auth/register", json={"email": email, "password": password, "display_name": email.split("@")[0]})
    assert response.status_code == 200, response.text
    return response.json()
