from decimal import Decimal

from regret.engine.intent import validate_intent
from regret.engine.market_analysis import MarketAnalysis
from regret.engine.risk import RiskEngine
from regret.engine.rules import RuleEngine, RuleSpec
from regret.types import RuleResultStatus, RuleSeverity, RuleType


def _risk(notional="2000", stop="90"):
    intent = validate_intent(symbol="NVDA", side="buy", notional=notional, stop_price=stop, target_price="130")
    return intent, RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("8000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )


def test_position_limit_fail():
    intent, risk = _risk("3000")
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
        market=MarketAnalysis(available=True),
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
    )
    assert evaluation.hard_failures
    check = evaluation.hard_failures[0]
    assert check.status == RuleResultStatus.FAIL
    payload = check.as_dict()
    assert payload["result"] == "FAILED"
    assert payload["actual"] == "30.0000"
    assert payload["required"] == "20"
    assert payload["threshold"] == "20"
    assert payload["difference"] == "10.0000"
    assert payload["rule_id"] == "r1"
    assert "exceeds" in payload["reason"].lower()


def test_position_limit_pass():
    intent, risk = _risk("1500")
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
        market=MarketAnalysis(available=True),
        daily_loss_pct=Decimal("0"),
        consecutive_losses=0,
    )
    assert not evaluation.hard_failures
    assert evaluation.checks[0].status == RuleResultStatus.PASS


def test_missing_history_is_unavailable_not_pass():
    intent, risk = _risk()
    rule = RuleSpec(
        id="r2",
        rule_type=RuleType.MAX_CONSECUTIVE_LOSSES,
        name="Losses",
        severity=RuleSeverity.HARD,
        threshold=Decimal("3"),
    )
    evaluation = RuleEngine().evaluate(
        rules=[rule],
        intent=intent,
        risk=risk,
        market=MarketAnalysis(available=True),
        daily_loss_pct=Decimal("0"),
        consecutive_losses=None,
    )
    assert evaluation.checks[0].status == RuleResultStatus.UNAVAILABLE
    assert evaluation.checks[0].as_dict()["result"] == "INSUFFICIENT DATA"
    assert evaluation.checks[0].actual is None
    assert evaluation.checks[0].difference is None
    assert not evaluation.hard_failures
