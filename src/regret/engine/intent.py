from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, Field

from regret.errors import ValidationFailed
from regret.types import OrderType, Side, dec


SYMBOL_RE = re.compile(r"\b([A-Z]{1,5})(?:/USD)?\b")
NOTIONAL_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I)
QTY_RE = re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:shares?|share|qty|units?)\b", re.I)
STOP_RE = re.compile(r"\b(?:stop|invalidation|invalid(?:ate)?)\s*(?:at|@|:)?\s*\$?\s*([0-9]+(?:\.[0-9]+)?)", re.I)
TARGET_RE = re.compile(r"\b(?:target|tp|take\s*profit)\s*(?:at|@|:)?\s*\$?\s*([0-9]+(?:\.[0-9]+)?)", re.I)
LIMIT_RE = re.compile(r"\b(?:limit)\s*(?:at|@|:)?\s*\$?\s*([0-9]+(?:\.[0-9]+)?)", re.I)
SIDE_BUY_RE = re.compile(r"\b(buy|long|accumulate)\b", re.I)
SIDE_SELL_RE = re.compile(r"\b(sell|short|exit|reduce)\b", re.I)
RESERVED = {
    "I", "A", "THE", "OF", "TO", "BUY", "SELL", "LONG", "SHORT", "USD", "STOP",
    "TARGET", "LIMIT", "WANT", "SHARES", "SHARE", "QTY", "FOR", "AND", "WITH",
}


class ParsedIntent(BaseModel):
    symbol: str | None = None
    side: Side | None = None
    notional: Decimal | None = None
    quantity: Decimal | None = None
    order_type: OrderType | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    raw_text: str = ""
    parse_source: str = "structured"
    missing: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    def as_record(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side.value if self.side else None,
            "notional": str(self.notional) if self.notional is not None else None,
            "quantity": str(self.quantity) if self.quantity is not None else None,
            "order_type": self.order_type.value if self.order_type else None,
            "limit_price": str(self.limit_price) if self.limit_price is not None else None,
            "stop_price": str(self.stop_price) if self.stop_price is not None else None,
            "target_price": str(self.target_price) if self.target_price is not None else None,
            "parse_source": self.parse_source,
        }


def _money(raw: str) -> Decimal:
    return Decimal(raw.replace(",", ""))


def parse_trade_text(text: str) -> ParsedIntent:
    """Deterministic parser. Does not invent missing fields."""
    original = text.strip()
    intent = ParsedIntent(raw_text=original, parse_source="regex")
    if not original:
        intent.missing = ["symbol", "side", "size"]
        return intent

    upper = original.upper()
    symbols = [m.group(1) for m in SYMBOL_RE.finditer(upper) if m.group(1) not in RESERVED]
    if symbols:
        intent.symbol = symbols[0]

    if SIDE_SELL_RE.search(original):
        intent.side = Side.SELL
    elif SIDE_BUY_RE.search(original):
        intent.side = Side.BUY

    notional_match = NOTIONAL_RE.search(original)
    if notional_match:
        intent.notional = _money(notional_match.group(1))

    qty_match = QTY_RE.search(original)
    if qty_match:
        intent.quantity = Decimal(qty_match.group(1))

    stop_match = STOP_RE.search(original)
    if stop_match:
        intent.stop_price = Decimal(stop_match.group(1))

    target_match = TARGET_RE.search(original)
    if target_match:
        intent.target_price = Decimal(target_match.group(1))

    limit_match = LIMIT_RE.search(original)
    if limit_match:
        intent.limit_price = Decimal(limit_match.group(1))
        intent.order_type = OrderType.LIMIT

    if intent.symbol is None:
        intent.missing.append("symbol")
    if intent.side is None:
        intent.missing.append("side")
    if intent.notional is None and intent.quantity is None:
        intent.missing.append("size")
    return intent


def validate_intent(
    *,
    symbol: str | None,
    side: str | None,
    notional: Decimal | str | float | None = None,
    quantity: Decimal | str | float | None = None,
    order_type: str | None = None,
    limit_price: Decimal | str | float | None = None,
    stop_price: Decimal | str | float | None = None,
    target_price: Decimal | str | float | None = None,
) -> ParsedIntent:
    missing: list[str] = []
    notes: list[str] = []
    clean_symbol = (symbol or "").strip().upper()
    if not clean_symbol or not re.fullmatch(r"[A-Z]{1,5}(?:/USD)?", clean_symbol):
        missing.append("symbol")
        clean_symbol_out = None
    else:
        clean_symbol_out = clean_symbol

    side_out: Side | None = None
    if side:
        try:
            side_out = Side(side.lower())
        except ValueError:
            missing.append("side")
    else:
        missing.append("side")

    def parse_dec(value: Any, field: str) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            parsed = dec(value)
        except (InvalidOperation, ValueError):
            raise ValidationFailed(f"{field} is not a valid number.")
        if parsed is not None and parsed <= 0:
            raise ValidationFailed(f"{field} must be greater than zero.")
        return parsed

    notional_d = parse_dec(notional, "notional")
    quantity_d = parse_dec(quantity, "quantity")
    limit_d = parse_dec(limit_price, "limit_price")
    stop_d = parse_dec(stop_price, "stop_price")
    target_d = parse_dec(target_price, "target_price")

    if notional_d is None and quantity_d is None:
        missing.append("size")

    order_out: OrderType | None = None
    if order_type:
        try:
            order_out = OrderType(order_type.lower())
        except ValueError:
            raise ValidationFailed("Unsupported order type.")
    elif limit_d is not None:
        order_out = OrderType.LIMIT
    else:
        order_out = OrderType.MARKET

    if order_out == OrderType.LIMIT and limit_d is None:
        missing.append("limit_price")
        notes.append("Limit orders require a limit price.")

    return ParsedIntent(
        symbol=clean_symbol_out,
        side=side_out,
        notional=notional_d,
        quantity=quantity_d,
        order_type=order_out,
        limit_price=limit_d,
        stop_price=stop_d,
        target_price=target_d,
        parse_source="validated",
        missing=missing,
        notes=notes,
    )
