from decimal import Decimal

from regret.engine.market_analysis import Bar, analyze_bars


def test_insufficient_bars_unavailable():
    result = analyze_bars([])
    assert result.available is False
    assert result.trend is None
    assert result.last_close is None


def test_calculates_from_provided_bars_only():
    bars = []
    price = Decimal("100")
    for i in range(60):
        price += Decimal("0.5")
        bars.append(
            Bar(
                timestamp=str(i),
                open=price,
                high=price + Decimal("1"),
                low=price - Decimal("1"),
                close=price,
                volume=Decimal("1000"),
            )
        )
    result = analyze_bars(bars)
    assert result.available is True
    assert result.bar_count == 60
    assert result.last_close == bars[-1].close
    assert result.sma20 is not None
    assert result.trend in {"bullish", "bearish", "mixed", "neutral"}
    assert result.support == min(b.low for b in bars[-20:])
    assert result.resistance == max(b.high for b in bars[-20:])
