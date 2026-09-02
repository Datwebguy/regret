from sqlalchemy import select

from regret.brokers.alpaca import trading_base_url
from regret.models.alpaca_connection import AlpacaConnection
from regret.security import encrypt_str
from regret.services import connections
from regret.services.auth import register_user
from tests.conftest import register


def test_paper_and_live_hosts_are_separated():
    assert trading_base_url("paper") == "https://paper-api.alpaca.markets"
    assert trading_base_url("live") == "https://api.alpaca.markets"
    assert trading_base_url("paper") != trading_base_url("live")


def test_oauth_start_is_unavailable_when_not_configured(client):
    register(client, "oauth-start@example.com")
    response = client.post("/api/alpaca/oauth/start?environment=paper")
    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "oauth_not_configured"
    assert "ALPACA_" not in body["message"]


def test_status_without_connection_does_not_invent_an_account(client):
    register(client, "status-empty@example.com")
    body = client.get("/api/alpaca/status").json()
    assert body["connected"] is False
    assert body.get("account") in (None, {}, False) or "account" not in body or body.get("account") is None
    assert body.get("active") in (None, False) or body.get("active") is None
    blob = str(body)
    assert "equity" not in blob or body.get("account") is None


def test_unconnected_analysis_env_resolves_to_real_paper_connection(db):
    user = register_user(db, email="resolve@example.com", password="super-secret-pass")
    db.add(
        AlpacaConnection(
            user_id=user.id,
            environment="paper",
            method="oauth",
            access_token_encrypted=encrypt_str("stored-token-not-used-in-this-test"),
            status="active",
        )
    )
    db.flush()
    found = connections.connection_for_execution(db, user.id, "unconnected")
    assert found is not None
    assert found.environment == "paper"
    missing_live = connections.connection_for_execution(db, user.id, "live")
    assert missing_live is None


def test_preview_without_broker_does_not_invent_an_order(client):
    register(client, "preview-empty@example.com")
    analysis = client.post("/api/analyze", json={"text": "I want to buy $400 of AAPL"}).json()
    preview = client.post("/api/orders/preview", json={"analysis_id": analysis["analysis_id"]})
    assert preview.status_code in {409, 422}
    body = preview.json()
    assert body["error"] in {"alpaca_not_connected", "validation_failed"}
    assert "order" not in body
    assert body.get("submitted") is not True


def test_read_scopes_do_not_request_trading():
    assert connections.scopes_for_purpose("read") == "data"
    assert "trading" not in connections.scopes_for_purpose("read")
    assert "account:write" not in connections.scopes_for_purpose("read")
    assert connections.scopes_for_purpose("trade") == "data trading"
    assert "account:write" not in connections.scopes_for_purpose("trade")
    assert connections.DEFAULT_CONNECT_SCOPES == "data trading"


class _OAuthSettings:
    oauth_configured = True
    alpaca_oauth_client_id = "test-client-id"
    alpaca_oauth_client_secret = "test-client-secret-not-for-production"
    alpaca_oauth_redirect_uri = "http://127.0.0.1:8000/api/alpaca/callback"
    regret_live_trading_enabled = False
    regret_default_trading_environment = "paper"


def test_oauth_authorize_url_follows_official_paper_connect_flow(db):
    user = register_user(db, email="oauth-url@example.com", password="super-secret-pass")
    result = connections.begin_oauth(
        db,
        user.id,
        environment="paper",
        settings=_OAuthSettings(),
    )
    url = result["authorization_url"]
    assert url.startswith("https://app.alpaca.markets/oauth/authorize?")
    assert "response_type=code" in url
    assert "client_id=test-client-id" in url
    assert "env=paper" in url
    assert "scope=data+trading" in url or "scope=data%20trading" in url
    assert "account%3Awrite" not in url
    assert "account:write" not in url
    assert result["environment"] == "paper"
    assert result["scopes"] == "data trading"
    blob = str(result)
    assert "test-client-secret-not-for-production" not in blob
    assert "client_secret" not in blob
    assert "access_token" not in blob


def test_oauth_token_exchange_uses_official_token_host():
    assert connections.TOKEN_URL == "https://api.alpaca.markets/oauth/token"
    assert connections.AUTHORIZE_URL == "https://app.alpaca.markets/oauth/authorize"


def test_read_only_connection_cannot_send_orders():
    read_only = AlpacaConnection(user_id="u", environment="paper", method="oauth", scopes="data")
    trading = AlpacaConnection(user_id="u", environment="paper", method="oauth", scopes="data trading")
    assert connections.connection_can_trade(read_only) is False
    assert connections.connection_can_trade(trading) is True


def test_live_connection_rejected_when_live_is_disabled(db):
    from regret.errors import ForbiddenError
    import pytest

    user = register_user(db, email="live-block@example.com", password="super-secret-pass")
    with pytest.raises(ForbiddenError):
        connections.connect_with_api_keys(
            db,
            user_id=user.id,
            environment="live",
            api_key_id="not-used",
            api_secret="not-used",
        )


def test_broker_status_never_returns_secrets(client):
    register(client, "nosecrets@example.com")
    body = client.get("/api/alpaca/status").json()
    blob = str(body).lower()
    for forbidden in ("access_token", "refresh_token", "api_secret", "client_secret", "alpaca_secret"):
        assert forbidden not in blob
    assert "APCA-API" not in str(body)


def test_complete_oauth_never_creates_a_connection_from_a_fake_code(db):
    from regret.errors import IntegrationUnavailable, ValidationFailed
    import pytest

    with pytest.raises((IntegrationUnavailable, ValidationFailed)):
        connections.complete_oauth(db, code="not-a-real-code", state="missing-state")
    assert db.scalar(select(AlpacaConnection)) is None
