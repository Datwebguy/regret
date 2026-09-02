from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from regret.types import dec


TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")


def q(value: Decimal | None, places: Decimal = FOURPLACES) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(places, rounding=ROUND_HALF_UP)


def sma(values: Sequence[Decimal], window: int) -> Decimal | None:
    if window <= 0 or len(values) < window:
        return None
    chunk = values[-window:]
    return sum(chunk, Decimal("0")) / Decimal(window)


def roc(values: Sequence[Decimal], window: int) -> Decimal | None:
    if len(values) < window + 1:
        return None
    prev = values[-(window + 1)]
    if prev == 0:
        return None
    return (values[-1] - prev) / prev * Decimal("100")


def rsi(values: Sequence[Decimal], window: int = 14) -> Decimal | None:
    if len(values) < window + 1:
        return None
    gains = Decimal("0")
    losses = Decimal("0")
    recent = values[-(window + 1) :]
    for i in range(1, len(recent)):
        change = recent[i] - recent[i - 1]
        if change >= 0:
            gains += change
        else:
            losses += -change
    avg_gain = gains / Decimal(window)
    avg_loss = losses / Decimal(window)
    if avg_loss == 0:
        return Decimal("100") if avg_gain > 0 else Decimal("50")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def atr(highs: Sequence[Decimal], lows: Sequence[Decimal], closes: Sequence[Decimal], window: int = 14) -> Decimal | None:
    if len(highs) < window + 1 or len(lows) < window + 1 or len(closes) < window + 1:
        return None
    trs: list[Decimal] = []
    start = len(closes) - window
    for i in range(start, len(closes)):
        prev_close = closes[i - 1]
        high = highs[i]
        low = lows[i]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs, Decimal("0")) / Decimal(len(trs))


def realized_vol(closes: Sequence[Decimal], window: int = 20) -> Decimal | None:
    if len(closes) < window + 1:
        return None
    rets: list[Decimal] = []
    chunk = closes[-(window + 1) :]
    for i in range(1, len(chunk)):
        if chunk[i - 1] == 0:
            continue
        rets.append((chunk[i] - chunk[i - 1]) / chunk[i - 1])
    if len(rets) < 2:
        return None
    mean = sum(rets, Decimal("0")) / Decimal(len(rets))
    var = sum((r - mean) ** 2 for r in rets) / Decimal(len(rets) - 1)
    # annualize with 252 using Decimal
    daily = var.sqrt()
    return daily * Decimal("252").sqrt() * Decimal("100")


def pct_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return (current - previous) / previous * Decimal("100")


def safe_div(num: Decimal, den: Decimal) -> Decimal | None:
    if den == 0:
        return None
    return num / den


def as_decimal_list(values: Sequence[object]) -> list[Decimal]:
    out: list[Decimal] = []
    for value in values:
        parsed = dec(value)
        if parsed is None:
            raise ValueError("bar series contains a missing numeric value")
        out.append(parsed)
    return out
