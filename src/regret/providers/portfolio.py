from __future__ import annotations

from decimal import Decimal

from regret.brokers.base import PositionSnapshot


def exposure_pct(market_value: Decimal | None, equity: Decimal | None) -> Decimal | None:
    """Backend-owned share of equity. None means it cannot be calculated."""
    if market_value is None or equity is None or equity == 0:
        return None
    return abs(market_value) / equity * Decimal("100")


def with_exposure(position: PositionSnapshot, equity: Decimal | None) -> dict:
    payload = position.as_public_dict()
    pct = exposure_pct(position.market_value, equity)
    payload["exposure_pct"] = format(pct, "f") if pct is not None else None
    return payload


def concentration_after_trade(
    positions: list[PositionSnapshot],
    equity: Decimal | None,
    *,
    symbol: str,
    added_notional: Decimal | None,
    side: str | None,
) -> Decimal | None:
    """
    Largest single-name exposure after the proposed trade.

    Returns None if any required market value is missing. Does not fill gaps.
    """
    if equity is None or equity == 0:
        return None
    values: dict[str, Decimal] = {}
    for position in positions:
        if not position.symbol:
            continue
        if position.market_value is None:
            return None
        values[position.symbol.upper()] = abs(position.market_value)
    if added_notional is not None and symbol:
        key = symbol.upper()
        current = values.get(key, Decimal("0"))
        if (side or "").lower() == "sell":
            values[key] = abs(current - added_notional)
        else:
            values[key] = current + added_notional
    if not values:
        if added_notional is None:
            return None
        return abs(added_notional) / equity * Decimal("100")
    return max(values.values()) / equity * Decimal("100")
