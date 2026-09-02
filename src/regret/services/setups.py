from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.errors import DataUnavailable, IntegrationUnavailable, ValidationFailed
from regret.models.preferences import WatchlistSymbol
from regret.services import analysis as analysis_service
from regret.types import Verdict


def list_watchlist(db: Session, user_id: str) -> list[str]:
    rows = db.scalars(
        select(WatchlistSymbol).where(WatchlistSymbol.user_id == user_id).order_by(WatchlistSymbol.position.asc())
    ).all()
    return [r.symbol for r in rows]


def add_symbol(db: Session, user_id: str, symbol: str) -> list[str]:
    clean = symbol.strip().upper()
    if not clean:
        raise ValidationFailed("Symbol is required.")
    existing = list_watchlist(db, user_id)
    if clean not in existing:
        db.add(WatchlistSymbol(user_id=user_id, symbol=clean, position=len(existing)))
        db.flush()
        existing.append(clean)
    return existing


def remove_symbol(db: Session, user_id: str, symbol: str) -> list[str]:
    row = db.scalar(
        select(WatchlistSymbol).where(
            WatchlistSymbol.user_id == user_id,
            WatchlistSymbol.symbol == symbol.strip().upper(),
        )
    )
    if row:
        db.delete(row)
        db.flush()
    return list_watchlist(db, user_id)


def find_setups(db: Session, user_id: str, *, notional: str | None = None, side: str = "buy") -> dict:
    universe = list_watchlist(db, user_id)
    if not universe:
        return {
            "available": False,
            "message": "No setup universe is selected. Add symbols to your watchlist first. REGRET does not invent a stock list.",
            "setups": [],
        }
    setups = []
    errors = []
    size = notional or "1000"
    for symbol in universe:
        try:
            result = analysis_service.analyze_trade(
                db,
                user_id,
                symbol=symbol,
                side=side,
                notional=size,
            )
        except (DataUnavailable, IntegrationUnavailable, ValidationFailed) as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
            continue
        if result["verdict"] in {Verdict.BUY.value, Verdict.WAIT.value, Verdict.REDUCE.value}:
            setups.append(
                {
                    "symbol": symbol,
                    "verdict": result["verdict"],
                    "summary": result.get("summary"),
                    "analysis_id": result["analysis_id"],
                    "risk": (result.get("decision") or {}).get("risk"),
                    "market": {
                        "trend": ((result.get("decision") or {}).get("market") or {}).get("trend"),
                        "location": ((result.get("decision") or {}).get("market") or {}).get("price_location"),
                    },
                }
            )
    if not setups:
        return {
            "available": True,
            "message": "No setup currently matches your rules.",
            "setups": [],
            "errors": errors,
            "universe": universe,
        }
    return {"available": True, "setups": setups, "errors": errors, "universe": universe}
