from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.errors import IntegrationUnavailable, NotFoundError
from regret.models.alert import Alert, AlertEvent
from regret.models.thesis import TradeThesis
from regret.services import account as account_service
from regret.services import connections
from regret.services.orders import (
    CANCELLED_STATUSES,
    FILLED_STATUSES,
    OPEN_STATUSES,
    REJECTED_STATUSES,
    list_orders,
    serialize_order,
)
from regret.types import ThesisState, dec


def _bucket(status: str) -> str:
    value = (status or "").lower()
    if value in FILLED_STATUSES:
        return "filled"
    if value in CANCELLED_STATUSES:
        return "cancelled"
    if value in REJECTED_STATUSES:
        return "rejected"
    if value in OPEN_STATUSES or value in {"pending_new", "new", "accepted"}:
        return "open"
    if value in {"", "submitted"}:
        return "pending"
    return "other"


def broker_activity(db: Session, user_id: str) -> dict:
    """Live Alpaca book plus REGRET-submitted orders. Never invents state."""
    book = account_service.get_book(db, user_id)
    regret_orders = [serialize_order(row) for row in list_orders(db, user_id)]
    if not book.get("connected"):
        return {
            "available": False,
            "reason": book.get("reason") or "Portfolio check unavailable because no brokerage is connected.",
            "pending": [o for o in regret_orders if _bucket(o["status"]) == "pending"],
            "open": [],
            "filled": [o for o in regret_orders if o.get("filled")],
            "cancelled": [o for o in regret_orders if _bucket(o["status"]) == "cancelled"],
            "rejected": [o for o in regret_orders if _bucket(o["status"]) == "rejected"],
            "positions": [],
            "regret_orders": regret_orders,
        }

    grouped = {"pending": [], "open": [], "filled": [], "cancelled": [], "rejected": [], "other": []}
    conn = connections.connection_for_execution(db, user_id)
    live_orders = list(book.get("orders") or [])
    if conn is not None:
        try:
            extra = connections.provider_for(conn).get_orders(status="closed")
            live_orders = live_orders + [o.as_public_dict() for o in extra]
        except (IntegrationUnavailable, Exception):
            extra = []
    seen = set()
    for order in live_orders:
        key = order.get("id") or order.get("client_order_id")
        if key in seen:
            continue
        seen.add(key)
        grouped[_bucket(order.get("status") or "")].append(order)
    for order in regret_orders:
        grouped.setdefault(_bucket(order["status"]), []).append(order)

    return {
        "available": True,
        "source": "alpaca",
        "environment": book.get("environment"),
        "positions": book.get("positions") or [],
        "pending": grouped["pending"],
        "open": grouped["open"],
        "filled": grouped["filled"],
        "cancelled": grouped["cancelled"],
        "rejected": grouped["rejected"],
        "regret_orders": regret_orders,
    }


def list_theses(db: Session, user_id: str) -> list[dict]:
    rows = db.scalars(
        select(TradeThesis).where(TradeThesis.user_id == user_id).order_by(TradeThesis.created_at.desc())
    ).all()
    return [public_thesis(row) for row in rows]


def monitor_thesis(db: Session, user_id: str, thesis_id: str) -> dict:
    thesis = db.get(TradeThesis, thesis_id)
    if thesis is None or thesis.user_id != user_id:
        raise NotFoundError("Trade thesis not found.")
    return _evaluate(db, user_id, thesis)


def monitor_symbol(db: Session, user_id: str, symbol: str) -> dict:
    thesis = db.scalar(
        select(TradeThesis)
        .where(TradeThesis.user_id == user_id, TradeThesis.symbol == symbol.upper())
        .order_by(TradeThesis.created_at.desc())
    )
    if thesis is None:
        raise NotFoundError("No thesis exists for this symbol. Analyze and execute a trade first.")
    return _evaluate(db, user_id, thesis)


def _evaluate(db: Session, user_id: str, thesis: TradeThesis) -> dict:
    conn = connections.require_connection(db, user_id)
    provider = connections.provider_for(conn)
    positions = provider.get_positions()
    position = next((p for p in positions if p.symbol.upper() == thesis.symbol.upper()), None)

    price = None
    source = None
    ts = None
    bundle = provider.get_market_data(thesis.symbol)
    if bundle.quote and bundle.quote.mid is not None:
        price = bundle.quote.mid
        source = bundle.quote.source
        ts = bundle.quote.source_timestamp.isoformat() if bundle.quote.source_timestamp else None
    elif bundle.snapshot and bundle.snapshot.last_trade_price is not None:
        price = bundle.snapshot.last_trade_price
        source = bundle.snapshot.source
        ts = bundle.snapshot.last_trade_timestamp.isoformat() if bundle.snapshot.last_trade_timestamp else None
    if price is None:
        thesis.state = ThesisState.UNAVAILABLE.value
        thesis.last_review_json = json.dumps({"error": bundle.unavailable_reason})
        return {
            "thesis": public_thesis(thesis),
            "available": False,
            "message": bundle.unavailable_reason or "Market data unavailable.",
        }

    pnl = None
    pnl_pct = None
    if position and position.unrealized_pl is not None:
        pnl = position.unrealized_pl
        pnl_pct = position.unrealized_plpc
    elif price is not None and thesis.entry is not None and position and position.qty is not None:
        pnl = (price - Decimal(str(thesis.entry))) * position.qty
        if Decimal(str(thesis.entry)) != 0:
            pnl_pct = (price - Decimal(str(thesis.entry))) / Decimal(str(thesis.entry))

    dist_inv = None
    dist_tgt = None
    state = ThesisState.INTACT
    reasons: list[str] = []
    if price is not None and thesis.invalidation is not None:
        inv = Decimal(str(thesis.invalidation))
        dist_inv = price - inv if thesis.side == "buy" else inv - price
        if (thesis.side == "buy" and price <= inv) or (thesis.side == "sell" and price >= inv):
            state = ThesisState.INVALIDATED
            reasons.append("Price has reached the stored invalidation level.")
        elif thesis.entry is not None:
            entry = Decimal(str(thesis.entry))
            span = abs(entry - inv)
            if span and abs(price - inv) / span <= Decimal("0.2"):
                state = ThesisState.APPROACHING_INVALIDATION
                reasons.append("Price is within 20% of the remaining distance to invalidation.")
    if price is not None and thesis.target is not None:
        tgt = Decimal(str(thesis.target))
        dist_tgt = tgt - price if thesis.side == "buy" else price - tgt
        if (thesis.side == "buy" and price >= tgt) or (thesis.side == "sell" and price <= tgt):
            state = ThesisState.TARGET_REACHED
            reasons.append("Price has reached the stored target.")

    try:
        market_state = json.loads(thesis.market_conditions_json or "{}")
    except json.JSONDecodeError:
        market_state = {}
    original_trend = market_state.get("trend")
    # trend change requires bars; skip invention if unavailable
    review = {
        "current_price": format(price, "f") if price is not None else None,
        "price_source": source,
        "price_timestamp": ts,
        "position": position.as_public_dict() if position else None,
        "unrealized_pl": format(pnl, "f") if pnl is not None else None,
        "unrealized_plpc": format(pnl_pct, "f") if pnl_pct is not None else None,
        "distance_to_invalidation": format(dist_inv, "f") if dist_inv is not None else None,
        "distance_to_target": format(dist_tgt, "f") if dist_tgt is not None else None,
        "original_trend": original_trend,
        "state": state.value,
        "reasons": reasons,
    }
    thesis.state = state.value
    thesis.last_review_json = json.dumps(review)
    if state in {ThesisState.INVALIDATED, ThesisState.CHANGED, ThesisState.TARGET_REACHED}:
        _emit(
            db,
            user_id,
            kind="thesis_changed",
            symbol=thesis.symbol,
            message="The conditions behind this trade have changed. " + " ".join(reasons),
            payload=review,
        )
    return {"available": True, "thesis": public_thesis(thesis), "review": review}


def public_thesis(row: TradeThesis) -> dict:
    review = None
    if row.last_review_json:
        try:
            review = json.loads(row.last_review_json)
        except json.JSONDecodeError:
            review = None
    return {
        "id": row.id,
        "symbol": row.symbol,
        "side": row.side,
        "entry": str(row.entry) if row.entry is not None else None,
        "invalidation": str(row.invalidation) if row.invalidation is not None else None,
        "target": str(row.target) if row.target is not None else None,
        "risk_reward": str(row.risk_reward) if row.risk_reward is not None else None,
        "reason": row.reason,
        "state": row.state,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "last_review": review,
    }


def list_alerts(db: Session, user_id: str) -> list[dict]:
    events = db.scalars(
        select(AlertEvent).where(AlertEvent.user_id == user_id).order_by(AlertEvent.created_at.desc()).limit(50)
    ).all()
    return [
        {
            "id": e.id,
            "kind": e.kind,
            "symbol": e.symbol,
            "message": e.message,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "read_at": e.read_at.isoformat() if e.read_at else None,
        }
        for e in events
    ]


def configure_alert(db: Session, user_id: str, *, kind: str, symbol: str = "", threshold: str | None = None) -> dict:
    alert = Alert(user_id=user_id, kind=kind, symbol=symbol.upper(), threshold=dec(threshold) if threshold else None)
    db.add(alert)
    db.flush()
    return {"id": alert.id, "kind": alert.kind, "symbol": alert.symbol, "enabled": alert.enabled}


def _emit(db, user_id, *, kind, symbol, message, payload) -> None:
    db.add(
        AlertEvent(
            user_id=user_id,
            kind=kind,
            symbol=symbol,
            message=message,
            payload_json=json.dumps(payload, default=str),
        )
    )
