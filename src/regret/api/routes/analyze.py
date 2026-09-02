from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.user import User
from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.user import User
from regret.services import analysis as analysis_service
from regret.services import insights, setups
from decimal import Decimal

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeBody(BaseModel):
    text: str | None = None
    symbol: str | None = None
    side: str | None = None
    notional: str | None = None
    quantity: str | None = None
    order_type: str | None = None
    limit_price: str | None = None
    stop_price: str | None = None
    target_price: str | None = None
    propose_stop: bool = False
    parent_intent_id: str | None = None
    environment: str | None = None


class WatchBody(BaseModel):
    symbol: str


class SetupBody(BaseModel):
    notional: str | None = None
    side: str = "buy"


@router.post("/analyze")
def analyze(body: AnalyzeBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return analysis_service.analyze_trade(db, user.id, **body.model_dump())


@router.get("/analyses")
def analyses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rows = analysis_service.list_analyses(db, user.id)
    return {
        "analyses": [
            {
                "analysis_id": r.id,
                "verdict": r.verdict,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "environment": r.environment,
            }
            for r in rows
        ]
    }


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return analysis_service.serialize_analysis(analysis_service.get_analysis(db, user.id, analysis_id))


@router.get("/insights")
def get_insights(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return insights.behavior_insights(db, user.id)


@router.get("/setups")
def get_setups(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return setups.find_setups(db, user.id)


@router.post("/setups")
def run_setups(body: SetupBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return setups.find_setups(db, user.id, notional=body.notional, side=body.side)


@router.get("/watchlist")
def watchlist(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"symbols": setups.list_watchlist(db, user.id)}


@router.post("/watchlist")
def add_watch(body: WatchBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"symbols": setups.add_symbol(db, user.id, body.symbol)}


@router.delete("/watchlist/{symbol}")
def del_watch(symbol: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"symbols": setups.remove_symbol(db, user.id, symbol)}


class OptionsAnalyzeBody(BaseModel):
    """Request body for options strategy analysis."""
    symbols: list[str] | None = None  # Default: ["SPY", "QQQ"]
    min_iv_rank: int = 75  # Minimum IV Rank threshold (0-100)


@router.post("/analyze/options")
def analyze_options(
    body: OptionsAnalyzeBody,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Scan for IV Rank Reversion opportunities and generate AI proposals with risk gate validation."""
    from regret.brokers.alpaca import AlpacaCredentials
    from regret.services import account as account_service, connections
    from regret.services.options_strategy import OptionsStrategyService

    conn = connections.connection_for_execution(db, user.id, "paper")
    if conn:
        credentials = connections.credentials_for(conn)
    else:
        credentials = AlpacaCredentials(environment="paper", api_key_id="demo_key", api_secret="demo_secret")

    book = account_service.get_book(db, user.id)
    current_open_positions = len(book.get("positions") or [])
    portfolio_realized_loss = Decimal("0")

    service = OptionsStrategyService(credentials)
    return service.scan_and_propose(
        symbols=body.symbols or ["SPY", "QQQ", "IWM", "NVDA"],
        min_iv_rank=body.min_iv_rank,
        portfolio_realized_loss=portfolio_realized_loss,
        current_open_positions=current_open_positions,
    )


