from datetime import timedelta

from sqlalchemy import select

from regret.models.analysis import Analysis, Approval
from regret.models.alpaca_connection import AlpacaConnection
from regret.models.trade_intent import TradeIntent
from regret.models.user import SessionToken
from regret.security import utcnow
from regret.services import rate_limit
from regret.types import ApprovalStatus
from tests.conftest import register


BROWSER = {"Origin": "http://testserver"}


def test_browser_register_and_login_do_not_return_session_token(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "web@example.com", "password": "super-secret-pass"},
        headers=BROWSER,
    )
    assert created.status_code == 200
    assert "token" not in created.json()
    assert created.json()["user"]["email"] == "web@example.com"
    assert client.cookies.get("regret_session")
    assert client.get("/api/auth/me").status_code == 200

    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"email": "web@example.com", "password": "super-secret-pass"},
        headers=BROWSER,
    )
    assert login.status_code == 200
    assert "token" not in login.json()
    assert client.get("/api/auth/me").status_code == 200


def test_cli_login_still_receives_bearer_token(client):
    from fastapi.testclient import TestClient

    client.post(
        "/api/auth/register",
        json={"email": "cli@example.com", "password": "super-secret-pass"},
        headers={"X-Regret-Client": "cli"},
    )
    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"email": "cli@example.com", "password": "super-secret-pass"},
        headers={"X-Regret-Client": "cli"},
    )
    assert login.status_code == 200
    token = login.json()["token"]
    assert token
    bare = TestClient(client.app)
    me = bare.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "cli@example.com"


def test_login_creates_a_fresh_session_and_prevents_fixation(client, db):
    client.cookies.set("regret_session", "attacker-fixed-value")
    register(client, "rotate@example.com")
    values = [c.value for c in client.cookies.jar if c.name == "regret_session"]
    assert any(value != "attacker-fixed-value" for value in values)
    assert client.get("/api/auth/me").status_code == 200
    from regret.errors import UnauthorizedError
    from regret.services.auth import resolve_session
    import pytest

    with pytest.raises(UnauthorizedError):
        resolve_session(db, "attacker-fixed-value")


def test_fresh_login_issues_a_new_session_id(client, db):
    register(client, "fresh@example.com")
    first = db.scalar(select(SessionToken).where(SessionToken.revoked.is_(False)))
    assert first is not None
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "fresh@example.com", "password": "super-secret-pass"})
    db.expire_all()
    active = list(db.scalars(select(SessionToken).where(SessionToken.revoked.is_(False))).all())
    assert len(active) == 1
    assert active[0].id != first.id


def test_expired_session_is_rejected(client, db):
    register(client, "expire-session@example.com")
    row = db.scalar(select(SessionToken).where(SessionToken.revoked.is_(False)))
    row.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_revoked_session_is_rejected(client):
    register(client, "revoked@example.com")
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_failed_login_rate_limit_does_not_reveal_account(client, monkeypatch):
    from regret.config import reset_settings_cache

    monkeypatch.setenv("REGRET_LOGIN_FAIL_LIMIT_EMAIL", "3")
    monkeypatch.setenv("REGRET_LOGIN_FAIL_LIMIT_IP", "3")
    reset_settings_cache()
    rate_limit.limiter.reset()

    register(client, "limit@example.com")
    client.post("/api/auth/logout")
    last = None
    for _ in range(3):
        last = client.post(
            "/api/auth/login",
            json={"email": "limit@example.com", "password": "wrong-password-1"},
        )
        assert last.status_code == 401
        assert last.json()["message"] == "Email or password is incorrect."
    blocked = client.post(
        "/api/auth/login",
        json={"email": "limit@example.com", "password": "wrong-password-1"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "rate_limited"
    unknown = client.post(
        "/api/auth/login",
        json={"email": "nobody-limit@example.com", "password": "wrong-password-1"},
    )
    assert unknown.status_code in {401, 429}
    if unknown.status_code == 401:
        assert unknown.json()["message"] == "Email or password is incorrect."


def test_spoofed_forwarded_for_does_not_bypass_login_limit(client, monkeypatch):
    from regret.config import reset_settings_cache

    monkeypatch.setenv("REGRET_LOGIN_FAIL_LIMIT_EMAIL", "2")
    monkeypatch.setenv("REGRET_LOGIN_FAIL_LIMIT_IP", "100")
    reset_settings_cache()
    rate_limit.limiter.reset()
    register(client, "spoof@example.com")
    client.post("/api/auth/logout")
    for _ in range(2):
        client.post(
            "/api/auth/login",
            json={"email": "spoof@example.com", "password": "nope-nope-nope"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
    blocked = client.post(
        "/api/auth/login",
        json={"email": "spoof@example.com", "password": "nope-nope-nope"},
        headers={"X-Forwarded-For": "198.51.100.20"},
    )
    assert blocked.status_code == 429


def test_registration_abuse_limit(client, monkeypatch):
    from regret.config import reset_settings_cache

    monkeypatch.setenv("REGRET_REGISTER_LIMIT_IP", "2")
    reset_settings_cache()
    rate_limit.limiter.reset()
    assert client.post(
        "/api/auth/register",
        json={"email": "r1@example.com", "password": "super-secret-pass"},
    ).status_code == 200
    assert client.post(
        "/api/auth/register",
        json={"email": "r2@example.com", "password": "super-secret-pass"},
    ).status_code == 200
    third = client.post(
        "/api/auth/register",
        json={"email": "r3@example.com", "password": "super-secret-pass"},
    )
    assert third.status_code == 429


def test_cross_origin_state_change_is_rejected(client):
    register(client, "csrf@example.com")
    blocked = client.post(
        "/api/rules",
        json={"rule_type": "max_position_pct", "name": "No", "severity": "HARD", "threshold": "10"},
        headers={"Origin": "https://evil.example"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"] == "csrf_rejected"


def test_same_origin_state_change_works(client):
    register(client, "same@example.com")
    ok = client.post(
        "/api/rules",
        json={"rule_type": "max_position_pct", "name": "Yes", "severity": "HARD", "threshold": "10"},
        headers=BROWSER,
    )
    assert ok.status_code == 200


def test_oauth_callback_is_not_blocked_by_csrf(client):
    response = client.get("/api/alpaca/callback?code=x&state=y", follow_redirects=False)
    assert response.status_code in {302, 307}
    location = response.headers.get("location") or ""
    assert "/app/settings/broker?alpaca=" in location
    assert "csrf_rejected" not in location


def test_unauthenticated_confirm_fails(client):
    response = client.post("/api/orders/confirm", json={"approval_id": "missing", "confirm": True})
    assert response.status_code in {401, 404, 409}


def test_wrong_user_cannot_confirm_another_users_approval(client, db):
    register(client, "owner-order@example.com")
    from regret.services.auth import register_user

    owner = register_user(db, email="owner-db@example.com", password="super-secret-pass")
    intent = TradeIntent(user_id=owner.id, symbol="NVDA", side="buy", notional=1000, parse_source="test")
    db.add(intent)
    db.flush()
    analysis = Analysis(
        user_id=owner.id,
        intent_id=intent.id,
        analysis_version=1,
        engine_version="1.0.0",
        verdict="BUY",
        summary="ok",
        payload_json="{}",
        rule_snapshot_json="[]",
        environment="paper",
    )
    db.add(analysis)
    db.flush()
    approval = Approval(
        user_id=owner.id,
        analysis_id=analysis.id,
        intent_id=intent.id,
        status=ApprovalStatus.PENDING.value,
        expires_at=utcnow() + timedelta(minutes=5),
        preview_json="{}",
        client_order_id="regret-foreign",
    )
    db.add(approval)
    db.commit()

    client.post("/api/auth/logout")
    register(client, "thief-order@example.com")
    stolen = client.post("/api/orders/confirm", json={"approval_id": approval.id, "confirm": True})
    assert stolen.status_code in {404, 403}


def test_user_cannot_see_another_alpaca_connection(client, db):
    from regret.security import encrypt_str
    from regret.services.auth import register_user

    owner = register_user(db, email="alpaca-owner@example.com", password="super-secret-pass")
    db.add(
        AlpacaConnection(
            user_id=owner.id,
            environment="paper",
            method="oauth",
            access_token_encrypted=encrypt_str("not-a-real-token"),
            status="active",
        )
    )
    db.commit()
    register(client, "alpaca-stranger@example.com")
    status = client.get("/api/alpaca/status").json()
    assert status["connected"] is False
    assert status.get("account") is None
