from decimal import Decimal

from regret.engine.intent import parse_trade_text, validate_intent


def test_parse_notional_buy():
    parsed = parse_trade_text("I want to buy $2,000 of NVDA")
    assert parsed.symbol == "NVDA"
    assert parsed.side.value == "buy"
    assert parsed.notional == Decimal("2000")
    assert parsed.quantity is None
    assert parsed.stop_price is None


def test_parse_does_not_invent_stop():
    parsed = parse_trade_text("buy 10 shares of AAPL")
    assert parsed.symbol == "AAPL"
    assert parsed.quantity == Decimal("10")
    assert parsed.stop_price is None
    assert parsed.target_price is None


def test_validate_rejects_bad_symbol():
    parsed = validate_intent(symbol="not a symbol!!", side="buy", notional="100")
    assert "symbol" in parsed.missing


def test_validate_requires_size():
    parsed = validate_intent(symbol="MSFT", side="buy")
    assert "size" in parsed.missing
