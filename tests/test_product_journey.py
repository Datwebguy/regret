from tests.conftest import register


def test_new_user_can_analyze_without_alpaca_and_sees_no_fake_book(client):
    register(client, "trader@example.com")
    me = client.get("/api/auth/me")
    assert me.status_code == 200

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["connected"] is False
    assert portfolio["account"] is None
    assert portfolio["positions"] == []

    created = client.post(
        "/api/rules",
        json={
            "rule_type": "max_position_pct",
            "name": "Stay small",
            "severity": "HARD",
            "threshold": "20",
        },
    )
    assert created.status_code == 200

    analysis = client.post("/api/analyze", json={"text": "I want to buy $1000 of NVDA"})
    assert analysis.status_code == 200, analysis.text
    body = analysis.json()
    assert body["broker_connected"] is False
    assert body["account"] is None
    assert body["verdict"] in {"BUY", "WAIT", "REDUCE", "REJECT", "INCOMPLETE"}
    assert body["decision"]["portfolio"]["available"] is False
    assert body["decision"]["portfolio"]["reason"] == "Portfolio check unavailable because no brokerage is connected."
    assert body["decision"]["risk"]["equity"] is None
    assert body["decision"]["risk"]["buying_power"] is None

    names = [c["name"] for c in body["decision"]["rules"]["checks"]]
    assert "Stay small" in names
    stay = next(c for c in body["decision"]["rules"]["checks"] if c["name"] == "Stay small")
    assert stay["status"] == "UNAVAILABLE"
    assert stay["actual"] is None

    if body["verdict"] == "WAIT":
        assert body["decision"].get("next_condition")


def test_execution_cannot_skip_approval(client):
    register(client, "gate3@example.com")
    client.post("/api/analyze", json={"text": "I want to buy $500 of AAPL"})
    blocked = client.post("/api/orders/confirm", json={"approval_id": "nope", "confirm": False})
    assert blocked.status_code == 409
    assert blocked.json()["error"] == "approval_required"


def test_two_users_keep_separate_journals_and_rules(client):
    register(client, "left@example.com")
    client.post("/api/rules", json={"rule_type": "max_position_pct", "name": "Left rule", "severity": "HARD", "threshold": "10"})
    client.post("/api/analyze", json={"text": "buy $200 of MSFT"})
    left_journal = client.get("/api/journal").json()["entries"]
    assert left_journal

    client.post("/api/auth/logout")
    register(client, "right@example.com")
    rules = client.get("/api/rules").json()["rules"]
    assert rules == []
    journal = client.get("/api/journal").json()["entries"]
    assert journal == []
    stolen = client.get(f"/api/journal/{left_journal[0]['id']}")
    assert stolen.status_code == 404


def test_disconnected_pages_have_no_invented_money(client):
    register(client, "empty@example.com")
    for path in ("/api/account", "/api/portfolio", "/api/positions", "/api/broker-orders"):
        body = client.get(path).json()
        assert body.get("connected") is False
        assert body.get("account") in (None, {})
        if "positions" in body:
            assert body["positions"] == []
        if "orders" in body:
            assert body["orders"] == []
        blob = str(body)
        assert "10000" not in blob
        assert "fake" not in blob.lower()
