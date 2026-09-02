from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from regret.brokers.alpaca import AlpacaCredentials
from regret.providers.alpaca import AlpacaProvider
from tests.conftest import register

ACCOUNT_PAYLOAD = {
    "id": "904837e3-3b76-47ec-b432-046db621571b",
    "account_number": "PA123456",
    "status": "ACTIVE",
    "currency": "USD",
    "cash": "25000.50",
    "portfolio_value": "131000",
    "equity": "131000",
    "last_equity": "130000",
    "buying_power": "40000",
    "long_market_value": "31000",
    "short_market_value": "0",
    "trading_blocked": False,
    "transfers_blocked": False,
    "account_blocked": False,
    "pattern_day_trader": False,
    "trade_suspended_by_user": False,
}

POSITIONS_PAYLOAD = [
    {
        "symbol": "AAPL",
        "qty": "5",
        "side": "long",
        "avg_entry_price": "100.0",
        "market_value": "600.0",
        "cost_basis": "500.0",
        "unrealized_pl": "100.0",
        "unrealized_plpc": "0.20",
        "current_price": "120.0",
    }
]

ORDERS_PAYLOAD = [
    {
        "id": "order-1",
        "client_order_id": "regret-abc",
        "symbol": "MSFT",
        "side": "buy",
        "status": "accepted",
        "type": "market",
        "qty": "2",
        "notional": None,
        "filled_qty": "0",
        "filled_avg_price": None,
        "submitted_at": "2026-08-12T14:00:00Z",
        "filled_at": None,
    }
]


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.headers = {"X-Request-ID": "req-test"}
        self.content = b"{}" if payload is not None else b""

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, routes):
        self.routes = routes

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, **_kwargs):
        return self._respond(method.upper(), url)

    def get(self, url, **_kwargs):
        return self._respond("GET", url)

    def _respond(self, method, url):
        for key, payload in self.routes.items():
            verb, suffix = key
            if method == verb and url.endswith(suffix):
                return FakeResponse(payload)
        return FakeResponse({"message": "not found"}, status_code=404)


def _provider() -> AlpacaProvider:
    return AlpacaProvider(
        AlpacaCredentials(environment="paper", api_key_id="key", api_secret="secret"),
        account_access=True,
    )


def test_provider_maps_real_account_fields_and_keeps_missing_as_none():
    routes = {
        ("GET", "/v2/account"): {**ACCOUNT_PAYLOAD, "cash": None},
        ("GET", "/v2/positions"): POSITIONS_PAYLOAD,
        ("GET", "/v2/orders"): ORDERS_PAYLOAD,
    }
    with patch("regret.brokers.alpaca.httpx.Client", return_value=FakeClient(routes)):
        book = _provider().book()
    account = book["account"]
    assert book["connected"] is True
    assert book["source"] == "alpaca"
    assert account["status"] == "ACTIVE"
    assert account["equity"] == "131000"
    assert account["buying_power"] == "40000"
    assert account["portfolio_value"] == "131000"
    assert account["currency"] == "USD"
    assert account["trading_status"] == "enabled"
    assert account["cash"] is None
    assert account["cash"] != "0"
    assert book["positions"][0]["symbol"] == "AAPL"
    assert book["positions"][0]["qty"] == "5"
    assert book["positions"][0]["side"] == "long"
    assert book["positions"][0]["avg_entry_price"] == "100.0"
    assert book["positions"][0]["market_value"] == "600.0"
    assert book["positions"][0]["unrealized_pl"] == "100.0"
    assert book["positions"][0]["current_price"] == "120.0"
    assert Decimal(book["positions"][0]["exposure_pct"]) == Decimal("600.0") / Decimal("131000") * 100
    assert book["orders"][0]["id"] == "order-1"
    assert book["orders"][0]["symbol"] == "MSFT"


def test_provider_does_not_invent_zero_for_absent_financial_fields():
    routes = {
        ("GET", "/v2/account"): {
            "id": "acct",
            "account_number": "PA1",
            "status": "ACTIVE",
        },
        ("GET", "/v2/positions"): [
            {"symbol": "NVDA", "side": "long"}
        ],
        ("GET", "/v2/orders"): [],
    }
    with patch("regret.brokers.alpaca.httpx.Client", return_value=FakeClient(routes)):
        book = _provider().book()
    account = book["account"]
    for field in ("cash", "equity", "buying_power", "portfolio_value"):
        assert account[field] is None
    position = book["positions"][0]
    assert position["qty"] is None
    assert position["market_value"] is None
    assert position["avg_entry_price"] is None
    assert position["unrealized_pl"] is None
    assert position["current_price"] is None
    assert position["exposure_pct"] is None


def test_disconnected_book_does_not_invent_an_account(client):
    register(client, "provider-empty@example.com")
    body = client.get("/api/alpaca/book").json()
    assert body["connected"] is False
    assert body["account"] is None
    assert body["positions"] == []
    assert body["orders"] == []
    assert body["reason"] == "Portfolio check unavailable because no brokerage is connected."


def test_market_route_without_broker_does_not_invent_quotes(client):
    register(client, "market-empty@example.com")
    body = client.get("/api/market/quote/AAPL").json()
    assert body["available"] is False
    assert body.get("mid") in (None, False) or "mid" not in body
    assert "100" not in str(body.get("mid"))


def test_analyze_report_separates_sections_without_inventing_portfolio(client):
    register(client, "report@example.com")
    body = client.post("/api/analyze", json={"text": "I want to buy $500 of AAPL"}).json()
    report = body["report"]
    assert set(report) >= {"market", "setup", "rules", "portfolio", "risk", "why_not", "verdict"}
    assert report["portfolio"]["available"] is False
    assert report["portfolio"]["reason"] == "Portfolio check unavailable because no brokerage is connected."
    assert report["portfolio"]["account"] is None
    assert report["portfolio"]["positions"] == []
    assert report["risk"]["equity"] is None
    assert report["risk"]["buying_power"] is None
    assert report["verdict"]["value"] == body["verdict"]
    assert body["verdict"] == "INCOMPLETE"
    assert body["order_proposal"]["allowed"] is False
    assert body["market_data"]["symbol"] == "AAPL"
    assert body["market_data"]["available"] is False
    assert body["market_data"]["source"] in (None, "none")
