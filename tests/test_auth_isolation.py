from tests.conftest import register


def test_register_and_me(client):
    register(client, "one@example.com")
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "one@example.com"


def test_user_cannot_read_other_rules(client):
    register(client, "a@example.com")
    created = client.post(
        "/api/rules",
        json={"rule_type": "max_position_pct", "name": "A limit", "severity": "HARD", "threshold": "15"},
    )
    assert created.status_code == 200
    rule_id = created.json()["rule"]["id"]

    client.post("/api/auth/logout")
    register(client, "b@example.com")
    listed = client.get("/api/rules")
    assert listed.status_code == 200
    assert listed.json()["rules"] == []

    stolen = client.patch(f"/api/rules/{rule_id}", json={"threshold": "99"})
    assert stolen.status_code == 404


def test_unauthenticated_account_is_rejected(client):
    response = client.get("/api/account")
    assert response.status_code == 401


def test_no_portfolio_without_alpaca(client):
    register(client, "c@example.com")
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["account"] is None
    assert body["positions"] == []
    assert body["reason"] == "Portfolio check unavailable because no brokerage is connected."


def test_insights_empty_without_history(client):
    register(client, "d@example.com")
    response = client.get("/api/insights")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["insights"] == []
    assert "Not enough" in body["message"]


def test_journal_starts_empty(client):
    register(client, "e@example.com")
    response = client.get("/api/journal")
    assert response.status_code == 200
    assert response.json()["entries"] == []
