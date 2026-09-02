from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.user import User
from regret.services import connections

router = APIRouter(prefix="/api/market", tags=["market"])

MARKET_UNAVAILABLE = (
    "Market data is unavailable. Connect a brokerage to use live quotes and bars, "
    "or ask the operator to enable a market data source."
)


@router.get("/quote/{symbol}")
def quote(symbol: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    provider = connections.provider_for_user(db, user.id)
    if provider is None:
        return {
            "available": False,
            "symbol": symbol.strip().upper(),
            "message": MARKET_UNAVAILABLE,
        }
    bundle = provider.get_market_data(symbol)
    quote = bundle.quote
    if quote is None:
        return {
            **bundle.as_dict(),
            "available": False,
            "bid": None,
            "ask": None,
            "mid": None,
            "message": bundle.unavailable_reason or "No quote is currently available.",
        }
    return {
        **bundle.as_dict(),
        "available": True,
        "bid": format(quote.bid, "f") if quote.bid is not None else None,
        "ask": format(quote.ask, "f") if quote.ask is not None else None,
        "mid": format(quote.mid, "f") if quote.mid is not None else None,
    }


@router.get("/bars/{symbol}")
def bars(symbol: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    provider = connections.provider_for_user(db, user.id)
    if provider is None:
        return {
            "available": False,
            "symbol": symbol.strip().upper(),
            "bars": [],
            "message": MARKET_UNAVAILABLE,
        }
    bundle = provider.get_market_data(symbol)
    return {
        **bundle.as_dict(),
        "bars": [
            {
                "timestamp": b.timestamp,
                "open": format(b.open, "f"),
                "high": format(b.high, "f"),
                "low": format(b.low, "f"),
                "close": format(b.close, "f"),
                "volume": format(b.volume, "f"),
            }
            for b in bundle.bars
        ],
    }


@router.get("/news/{symbol}")
def news(symbol: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    provider = connections.provider_for_user(db, user.id)
    if provider is None:
        return {
            "available": False,
            "symbol": symbol.strip().upper(),
            "news": [],
            "message": MARKET_UNAVAILABLE,
        }
    bundle = provider.get_market_data(symbol)
    return {
        **bundle.as_dict(),
        "news": [
            {"id": n.id, "headline": n.headline, "source": n.source, "created_at": n.created_at, "url": n.url}
            for n in bundle.news
        ],
    }
