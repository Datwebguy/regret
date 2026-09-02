from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from regret.engine.indicators import atr, pct_change, q, realized_vol, roc, rsi, sma
from regret.types import dec


class Bar(BaseModel):
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    model_config = {"arbitrary_types_allowed": True}


class MarketAnalysis(BaseModel):
    available: bool
    unavailable_reason: str = ""
    bar_count: int = 0
    last_close: Decimal | None = None
    prev_close: Decimal | None = None
    daily_change_pct: Decimal | None = None
    sma20: Decimal | None = None
    sma50: Decimal | None = None
    rsi14: Decimal | None = None
    roc10: Decimal | None = None
    atr14: Decimal | None = None
    atr_pct: Decimal | None = None
    realized_vol_20: Decimal | None = None
    volume: Decimal | None = None
    avg_volume_20: Decimal | None = None
    volume_ratio: Decimal | None = None
    high20: Decimal | None = None
    low20: Decimal | None = None
    location: Decimal | None = None
    support: Decimal | None = None
    resistance: Decimal | None = None
    trend: str | None = None
    trend_basis: str = ""
    momentum: str | None = None
    momentum_basis: str = ""
    volatility: str | None = None
    volatility_basis: str = ""
    price_location: str | None = None
    location_basis: str = ""
    proposed_stop: Decimal | None = None
    proposed_stop_basis: str = ""
    proposed_target: Decimal | None = None
    proposed_target_basis: str = ""

    model_config = {"arbitrary_types_allowed": True}

    def as_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        for key, value in list(data.items()):
            if isinstance(value, Decimal):
                data[key] = format(value, "f")
        return data


def analyze_bars(bars: list[Bar]) -> MarketAnalysis:
    if len(bars) < 5:
        return MarketAnalysis(
            available=False,
            unavailable_reason="Insufficient historical bars to calculate market structure.",
            bar_count=len(bars),
        )

    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    volumes = [b.volume for b in bars]
    last = closes[-1]
    prev = closes[-2]
    daily = pct_change(last, prev)

    sma20_v = sma(closes, 20)
    sma50_v = sma(closes, 50)
    rsi_v = rsi(closes, 14)
    roc_v = roc(closes, 10)
    atr_v = atr(highs, lows, closes, 14)
    atr_pct = (atr_v / last * Decimal("100")) if atr_v is not None and last != 0 else None
    rvol = realized_vol(closes, 20)

    window20 = min(20, len(closes))
    high20 = max(highs[-window20:])
    low20 = min(lows[-window20:])
    loc = None
    if high20 != low20:
        loc = (last - low20) / (high20 - low20)

    avg_vol = sma(volumes, min(20, len(volumes)))
    vol_ratio = (volumes[-1] / avg_vol) if avg_vol and avg_vol != 0 else None

    trend, trend_basis = _trend(last, sma20_v, sma50_v)
    momentum, mom_basis = _momentum(roc_v, rsi_v)
    vol_label, vol_basis = _volatility(atr_pct, rvol)
    loc_label, loc_basis = _location(loc, last, high20, low20)

    proposed_stop = None
    proposed_stop_basis = ""
    if low20 is not None:
        proposed_stop = low20
        proposed_stop_basis = f"20-session low ({format(low20, 'f')}) used as a proposed invalidation. This is derived from available bars, not a guaranteed level."
        if atr_v is not None:
            atr_stop = last - (atr_v * Decimal("1.5"))
            proposed_stop_basis += f" ATR(14)={format(atr_v, 'f')}; 1.5×ATR below last close would be {format(atr_stop, 'f')}."

    proposed_target = None
    proposed_target_basis = ""
    if high20 is not None and last < high20:
        proposed_target = high20
        proposed_target_basis = f"20-session high ({format(high20, 'f')}) used as a proposed target from available bars."

    return MarketAnalysis(
        available=True,
        bar_count=len(bars),
        last_close=q(last),
        prev_close=q(prev),
        daily_change_pct=q(daily),
        sma20=q(sma20_v),
        sma50=q(sma50_v),
        rsi14=q(rsi_v),
        roc10=q(roc_v),
        atr14=q(atr_v),
        atr_pct=q(atr_pct),
        realized_vol_20=q(rvol),
        volume=q(volumes[-1], Decimal("0.0001")),
        avg_volume_20=q(avg_vol, Decimal("0.0001")),
        volume_ratio=q(vol_ratio),
        high20=q(high20),
        low20=q(low20),
        location=q(loc),
        support=q(low20),
        resistance=q(high20),
        trend=trend,
        trend_basis=trend_basis,
        momentum=momentum,
        momentum_basis=mom_basis,
        volatility=vol_label,
        volatility_basis=vol_basis,
        price_location=loc_label,
        location_basis=loc_basis,
        proposed_stop=q(proposed_stop),
        proposed_stop_basis=proposed_stop_basis,
        proposed_target=q(proposed_target),
        proposed_target_basis=proposed_target_basis,
    )


def _trend(last: Decimal, sma20: Decimal | None, sma50: Decimal | None) -> tuple[str | None, str]:
    if sma20 is None:
        return None, "Need at least 20 daily bars to calculate SMA20."
    if sma50 is None:
        if last > sma20:
            return "bullish", "Close is above SMA20. SMA50 unavailable (need 50 bars)."
        if last < sma20:
            return "bearish", "Close is below SMA20. SMA50 unavailable (need 50 bars)."
        return "neutral", "Close equals SMA20. SMA50 unavailable."
    if last > sma20 > sma50:
        return "bullish", "Close > SMA20 > SMA50."
    if last < sma20 < sma50:
        return "bearish", "Close < SMA20 < SMA50."
    return "mixed", "SMA alignment is mixed (close, SMA20, SMA50 are not stacked)."


def _momentum(roc_v: Decimal | None, rsi_v: Decimal | None) -> tuple[str | None, str]:
    parts = []
    if roc_v is not None:
        parts.append(f"10-session ROC={format(roc_v, 'f')}%")
    if rsi_v is not None:
        parts.append(f"RSI14={format(rsi_v, 'f')}")
    if roc_v is None and rsi_v is None:
        return None, "Need at least 15 daily bars for RSI and 11 for ROC."
    label = "neutral"
    if roc_v is not None and roc_v >= Decimal("3") and (rsi_v is None or rsi_v >= Decimal("55")):
        label = "strong"
    elif roc_v is not None and roc_v <= Decimal("-3") and (rsi_v is None or rsi_v <= Decimal("45")):
        label = "weak"
    elif rsi_v is not None and rsi_v >= Decimal("70"):
        label = "overbought"
    elif rsi_v is not None and rsi_v <= Decimal("30"):
        label = "oversold"
    return label, "; ".join(parts)


def _volatility(atr_pct: Decimal | None, rvol: Decimal | None) -> tuple[str | None, str]:
    parts = []
    if atr_pct is not None:
        parts.append(f"ATR(14)/price={format(atr_pct, 'f')}%")
    if rvol is not None:
        parts.append(f"20-session realized vol (ann.)={format(rvol, 'f')}%")
    if atr_pct is None:
        return None, "Need at least 15 daily bars for ATR."
    if atr_pct >= Decimal("3"):
        label = "high"
    elif atr_pct <= Decimal("1"):
        label = "low"
    else:
        label = "moderate"
    return label, "; ".join(parts)


def _location(loc: Decimal | None, last: Decimal, high20: Decimal, low20: Decimal) -> tuple[str | None, str]:
    basis = f"Close={format(last, 'f')} vs 20-session high={format(high20, 'f')} / low={format(low20, 'f')}"
    if loc is None:
        return None, "20-session high and low are equal; location cannot be calculated."
    if loc >= Decimal("0.85"):
        return "near resistance", basis
    if loc <= Decimal("0.15"):
        return "near support", basis
    return "mid-range", basis
