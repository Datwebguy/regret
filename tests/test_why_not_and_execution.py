from decimal import Decimal

from regret.engine.decision import DecisionEngine
from regret.engine.intent import validate_intent
from regret.engine.market_analysis import Bar, analyze_bars
from regret.engine.risk import RiskEngine
from regret.engine.rules import RuleEngine, RuleSpec
from regret.engine.why_not import WhyNotEngine
from regret.services.proposal import build_order_proposal
from regret.types import RuleSeverity, RuleType, Verdict
from tests.conftest import register


def _bars(closes: list[float]) -> list[Bar]:
    bars = []
    for i, close in enumerate(closes):
        c = Decimal(str(close))
        bars.append(Bar(timestamp=str(i), open=c, high=c + Decimal("1"), low=c - Decimal("1"), close=c, volume=Decimal("1000")))
    return bars


def test_why_not_includes_actual_and_required_from_rules():
    intent = validate_intent(symbol="NVDA", side="buy", notional="3000", stop_price="90", target_price="130")
    risk = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    rule = RuleSpec(
        id="r1",
        rule_type=RuleType.MAX_POSITION_PCT,
        name="Max position",
        severity=RuleSeverity.HARD,
        threshold=Decimal("20"),
    )
    evaluation = RuleEngine().evaluate(
        rules=[rule],
        intent=intent,
        risk=risk,
        market=analyze_bars(_bars([100] * 30)),
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
    )
    why = WhyNotEngine().evaluate(
        intent=intent,
        market=analyze_bars(_bars([100] * 30)),
        risk=risk,
        rules=evaluation,
    )
    item = next(i for i in why.items if i.rule_id == "r1")
    payload = item.as_dict()
    assert payload["title"] == "Portfolio concentration"
    assert payload["actual"] == "30.0000"
    assert payload["required"] == "20"
    assert payload["difference"] == "10.0000"


def test_incomplete_when_market_data_missing():
    intent = validate_intent(symbol="NVDA", side="buy", notional="500")
    market = analyze_bars([])
    risk = RiskEngine().calculate(
        intent=intent,
        equity=None,
        buying_power=None,
        entry_price=None,
        existing_position_qty=None,
        existing_position_value=None,
    )
    decision = DecisionEngine().decide(
        intent=intent,
        market=market,
        risk=risk,
        rules=[],
        daily_loss_pct=None,
        consecutive_losses=None,
        data_fresh=True,
        freshness_message="none",
        market_open=None,
        news_headlines=[],
        asset_tradable=None,
    )
    assert decision.verdict == Verdict.INCOMPLETE
    assert decision.as_dict()["incomplete"] is True
    proposal = build_order_proposal(intent=intent, decision=decision, entry_source=None, broker_connected=False)
    assert proposal["allowed"] is False
    assert proposal["submitted"] is False


def test_order_proposal_not_submitted_when_buy_possible():
    closes = [90 + i * 0.2 for i in range(60)]
    intent = validate_intent(symbol="NVDA", side="buy", notional="500", stop_price="80", target_price="140")
    market = analyze_bars(_bars(closes))
    risk = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal(str(closes[-1])),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    decision = DecisionEngine().decide(
        intent=intent,
        market=market,
        risk=risk,
        rules=[],
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
        data_fresh=True,
        freshness_message="ok",
        market_open=True,
        news_headlines=[],
        asset_tradable=True,
    )
    if decision.verdict in {Verdict.BUY, Verdict.WAIT, Verdict.REDUCE}:
        proposal = build_order_proposal(intent=intent, decision=decision, entry_source="quote_mid", broker_connected=True)
        assert proposal["allowed"] is True
        assert proposal["submitted"] is False
        assert proposal["symbol"] == "NVDA"
        assert proposal["approval_required"] is True


def test_analyze_includes_proposal_and_structured_why_not(client):
    register(client, "why@example.com")
    body = client.post("/api/analyze", json={"text": "I want to buy $500 of AAPL"}).json()
    assert "order_proposal" in body
    assert body["order_proposal"]["submitted"] is False
    assert "why_not" in body["decision"]
    assert "items" in body["decision"]["why_not"]
    assert body["analysis_id"]
    assert "inputs_used" in body


def test_incomplete_cannot_be_previewed(client):
    register(client, "noprev@example.com")
    analysis = client.post("/api/analyze", json={"text": "I want to buy $500 of AAPL"}).json()
    if analysis["verdict"] == "INCOMPLETE":
        preview = client.post("/api/orders/preview", json={"analysis_id": analysis["analysis_id"]})
        assert preview.status_code == 422


def test_journal_snapshot_is_frozen(client):
    register(client, "journal-freeze@example.com")
    client.post("/api/rules", json={"rule_type": "max_position_pct", "name": "Stay small", "severity": "HARD", "threshold": "20"})
    client.post("/api/analyze", json={"text": "buy $200 of MSFT"})
    entries = client.get("/api/journal").json()["entries"]
    assert entries
    detail = client.get(f"/api/journal/{entries[0]['id']}").json()
    names = [r["name"] for r in (detail.get("snapshot") or {}).get("rules_at_the_time") or []]
    assert "Stay small" in names
    client.post("/api/rules", json={"rule_type": "max_position_pct", "name": "Later rule", "severity": "HARD", "threshold": "5"})
    again = client.get(f"/api/journal/{entries[0]['id']}").json()
    later_names = [r["name"] for r in (again.get("snapshot") or {}).get("rules_at_the_time") or []]
    assert "Stay small" in later_names
    assert "Later rule" not in later_names


def test_order_serialize_does_not_claim_fill():
    from regret.models.order import BrokerOrder
    from regret.services.orders import serialize_order

    row = BrokerOrder(
        id="exec-1",
        user_id="u",
        approval_id="a",
        analysis_id="an",
        intent_id="i",
        environment="paper",
        alpaca_order_id="alp-1",
        client_order_id="regret-1",
        symbol="NVDA",
        side="buy",
        status="accepted",
    )
    payload = serialize_order(row)
    assert payload["status"] == "accepted"
    assert payload["filled"] is False
    assert payload["executed"] is False
    assert payload["execution_id"] == row.id


def test_disconnected_monitor_does_not_invent_orders(client):
    register(client, "mon@example.com")
    body = client.get("/api/monitor").json()
    assert body["available"] is False
    assert body["positions"] == []
    assert body["open"] == []
