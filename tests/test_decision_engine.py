from decimal import Decimal

from regret.engine.decision import DecisionEngine
from regret.engine.intent import validate_intent
from regret.engine.market_analysis import Bar, analyze_bars
from regret.engine.risk import RiskEngine
from regret.engine.rules import RuleSpec
from regret.types import RuleSeverity, RuleType, Verdict


def _bars(closes: list[float]) -> list[Bar]:
    bars = []
    for i, close in enumerate(closes):
        c = Decimal(str(close))
        bars.append(Bar(timestamp=str(i), open=c, high=c + Decimal("1"), low=c - Decimal("1"), close=c, volume=Decimal("1000")))
    return bars


def test_hard_rule_reject():
    intent = validate_intent(symbol="NVDA", side="buy", notional="4000")
    market = analyze_bars(_bars([100 + i * 0.1 for i in range(30)]))
    risk = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    rules = [
        RuleSpec(id="1", rule_type=RuleType.MAX_DAILY_LOSS_PCT, name="Daily loss", severity=RuleSeverity.HARD, threshold=Decimal("3"))
    ]
    decision = DecisionEngine().decide(
        intent=intent,
        market=market,
        risk=risk,
        rules=rules,
        daily_loss_pct=Decimal("-4"),
        consecutive_losses=0,
        data_fresh=True,
        freshness_message="ok",
        market_open=True,
        news_headlines=[],
        asset_tradable=True,
    )
    assert decision.verdict == Verdict.REJECT
    assert decision.blocked is True


def test_reduce_when_size_too_large():
    intent = validate_intent(symbol="NVDA", side="buy", notional="4000")
    market = analyze_bars(_bars([100] * 30))
    risk = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    rules = [
        RuleSpec(id="1", rule_type=RuleType.MAX_POSITION_PCT, name="Max pos", severity=RuleSeverity.HARD, threshold=Decimal("20"))
    ]
    decision = DecisionEngine().decide(
        intent=intent,
        market=market,
        risk=risk,
        rules=rules,
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
        data_fresh=True,
        freshness_message="ok",
        market_open=True,
        news_headlines=[],
        asset_tradable=True,
    )
    assert decision.verdict == Verdict.REDUCE
    assert decision.suggested_notional == Decimal("2000")


def test_stale_data_blocks():
    intent = validate_intent(symbol="NVDA", side="buy", notional="500")
    market = analyze_bars(_bars([100] * 30))
    risk = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal("100"),
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
        data_fresh=False,
        freshness_message="stale",
        market_open=True,
        news_headlines=[],
        asset_tradable=True,
    )
    assert decision.verdict == Verdict.REJECT
    assert decision.blocked is True
    assert "not fresh" in decision.blocked_reason.lower() or "stale" in decision.reasons[0].lower()


def test_buy_when_inputs_pass():
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
    rules = [
        RuleSpec(id="1", rule_type=RuleType.MAX_POSITION_PCT, name="Max pos", severity=RuleSeverity.HARD, threshold=Decimal("20"))
    ]
    decision = DecisionEngine().decide(
        intent=intent,
        market=market,
        risk=risk,
        rules=rules,
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
        data_fresh=True,
        freshness_message="ok",
        market_open=True,
        news_headlines=[],
        asset_tradable=True,
    )
    assert decision.verdict in {Verdict.BUY, Verdict.WAIT}
    assert decision.approval_required is True
