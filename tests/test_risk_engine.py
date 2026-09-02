from decimal import Decimal

from regret.engine.intent import validate_intent
from regret.engine.risk import RiskEngine


def test_risk_from_actual_inputs():
    intent = validate_intent(symbol="NVDA", side="buy", notional="2000", stop_price="90", target_price="130")
    result = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("4000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    assert result.available is True
    assert result.quantity == Decimal("20.00000000")
    assert result.portfolio_percentage_after == Decimal("20.0000")
    assert result.risk_dollars == Decimal("200.0000")
    assert result.risk_percentage == Decimal("2.0000")
    assert result.reward_dollars == Decimal("600.0000")
    assert result.risk_reward == Decimal("3.0000")
    assert result.buying_power_sufficient is True


def test_missing_stop_does_not_invent_risk():
    intent = validate_intent(symbol="NVDA", side="buy", notional="2000")
    result = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("4000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    assert result.risk_dollars is None
    assert result.risk_percentage is None
    assert "stop_price" in result.missing_inputs
    assert "invalidation" in result.unavailable_reason.lower() or "stop" in result.unavailable_reason.lower()


def test_insufficient_buying_power():
    intent = validate_intent(symbol="NVDA", side="buy", notional="5000")
    result = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("1000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    assert result.buying_power_sufficient is False


def test_missing_equity_is_unavailable():
    intent = validate_intent(symbol="NVDA", side="buy", notional="1000")
    result = RiskEngine().calculate(
        intent=intent,
        equity=None,
        buying_power=None,
        entry_price=Decimal("100"),
        existing_position_qty=None,
        existing_position_value=None,
    )
    assert result.available is False
    assert result.unavailable_reason.startswith("INSUFFICIENT DATA")
    assert "equity" in result.unavailable_reason.lower()
    assert result.existing_position_value is None
    assert result.post_trade_exposure is None
    assert result.portfolio_percentage_after is None


def test_missing_position_is_not_converted_to_zero():
    intent = validate_intent(symbol="NVDA", side="buy", notional="1000")
    result = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("4000"),
        entry_price=Decimal("100"),
        existing_position_qty=None,
        existing_position_value=None,
    )
    assert result.existing_position_qty is None
    assert result.existing_position_value is None
    assert result.post_trade_exposure is None
    assert result.portfolio_percentage_after is None
    assert result.cash_impact is None


def test_zero_position_is_kept_when_broker_returned_zero():
    intent = validate_intent(symbol="NVDA", side="buy", notional="1000")
    result = RiskEngine().calculate(
        intent=intent,
        equity=Decimal("10000"),
        buying_power=Decimal("4000"),
        entry_price=Decimal("100"),
        existing_position_qty=Decimal("0"),
        existing_position_value=Decimal("0"),
    )
    assert result.existing_position_qty == Decimal("0.00000000")
    assert result.existing_position_value == Decimal("0.0000")
    assert result.portfolio_percentage_after == Decimal("10.0000")
