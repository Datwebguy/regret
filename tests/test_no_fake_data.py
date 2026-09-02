from tests.conftest import register


def test_analyze_without_connection_still_returns_a_real_analysis(client):
    register(client, "nofake@example.com")
    response = client.post("/api/analyze", json={"text": "I want to buy $1000 of AAPL"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verdict"] in {"BUY", "WAIT", "REDUCE", "REJECT", "INCOMPLETE"}
    assert body["broker_connected"] is False
    assert body["account"] is None
    assert body["capabilities"]["portfolio"] is False
    assert body["capabilities"]["execution"] is False
    decision = body["decision"]
    assert decision["portfolio"]["available"] is False
    assert decision["portfolio"]["reason"] == "Portfolio check unavailable because no brokerage is connected."
    assert body.get("positions") == []
    assert body.get("orders") == []
    assert body.get("report", {}).get("verdict", {}).get("value") == body["verdict"]
    assert "equity" not in (body.get("account") or {})


def test_analyze_without_connection_does_not_invent_balances(client):
    register(client, "nobals@example.com")
    body = client.post("/api/analyze", json={"text": "I want to buy $1000 of AAPL"}).json()
    assert body.get("account") is None
    risk = body["decision"]["risk"]
    assert risk.get("equity") is None
    assert risk.get("buying_power") is None


def test_setups_without_watchlist_does_not_invent_symbols(client):
    register(client, "nowatch@example.com")
    response = client.get("/api/setups")
    assert response.status_code == 200
    body = response.json()
    assert body["setups"] == []
    assert "watchlist" in body["message"].lower() or "universe" in body["message"].lower()


def test_broker_status_does_not_expose_env_var_names(client):
    client.post("/api/auth/register", json={"email": "oauth@example.com", "password": "super-secret-pass"})
    alpaca = client.get("/api/alpaca/status").json()
    assert alpaca["connected"] is False
    assert alpaca["connect_available"] is False
    blob = str(alpaca)
    assert "ALPACA_OAUTH" not in blob
    assert "activation" not in alpaca
