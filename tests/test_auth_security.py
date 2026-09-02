"""Security properties of REGRET authentication that were previously untested."""

from sqlalchemy import select

from regret.models.user import SessionToken, User
from tests.conftest import register


def test_password_is_stored_as_bcrypt_hash_not_plaintext(db, client):
    register(client, "hash@example.com", password="super-secret-pass")
    user = db.scalar(select(User).where(User.email == "hash@example.com"))
    assert user is not None
    assert user.password_hash != "super-secret-pass"
    assert user.password_hash.startswith("$2")
    assert "super-secret-pass" not in user.password_hash


def test_wrong_password_is_rejected(client):
    register(client, "wrong@example.com", password="super-secret-pass")
    client.post("/api/auth/logout")
    response = client.post(
        "/api/auth/login",
        json={"email": "wrong@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401
    assert "super-secret-pass" not in response.text


def test_logout_invalidates_the_server_session(client, db):
    register(client, "logout@example.com")
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    after = client.get("/api/auth/me")
    assert after.status_code == 401
    token = db.scalar(select(SessionToken).where(SessionToken.revoked.is_(True)))
    assert token is not None


def test_unauthenticated_requests_are_rejected(client):
    for path in (
        "/api/auth/me",
        "/api/account",
        "/api/portfolio",
        "/api/analyses",
        "/api/journal",
        "/api/orders",
        "/api/rules",
        "/api/alpaca/status",
        "/api/preferences",
    ):
        response = client.get(path)
        assert response.status_code == 401, path


def test_user_cannot_read_another_users_analysis(client):
    register(client, "owner@example.com")
    analysis = client.post("/api/analyze", json={"text": "I want to buy $200 of MSFT"}).json()
    analysis_id = analysis["analysis_id"]
    client.post("/api/auth/logout")
    register(client, "intruder@example.com")
    stolen = client.get(f"/api/analyses/{analysis_id}")
    assert stolen.status_code == 404
