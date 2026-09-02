from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.config import get_settings
from regret.db.session import get_db
from regret.errors import IntegrationUnavailable, ValidationFailed
from regret.models.user import User
from regret.services import account as account_service
from regret.services import connections

router = APIRouter(prefix="/api/alpaca", tags=["alpaca"])


class KeyConnectBody(BaseModel):
    environment: str = "paper"
    api_key_id: str
    api_secret: str


@router.get("/status")
def status(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    listed = [connections.public_connection(c) for c in connections.list_connections(db, user.id)]
    active = connections.get_connection(db, user.id)
    if active is None:
        status = connections.oauth_status()
        status["connected"] = False
        status["reachable"] = False
        status["active"] = None
        status["account"] = None
        status["connections"] = listed
        status["capabilities"] = _capabilities(status, None)
        return status
    status = connections.verify_connection(db, user.id)
    status["connections"] = listed
    status["capabilities"] = _capabilities(status, status.get("active"))
    return status


def _capabilities(status: dict, active: dict | None) -> dict:
    return {
        "analyze": True,
        "portfolio": bool(active),
        "market_data": bool(active) or bool(status.get("connected")),
        "trading": bool(active and active.get("can_trade")),
        "live": bool(status.get("live_trading_enabled")),
        "paper": True,
    }


@router.post("/oauth/start")
def oauth_start(
    environment: str = Query(default="paper"),
    purpose: str = Query(default="trade"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return connections.begin_oauth(db, user.id, environment=environment, purpose=purpose)


@router.get("/callback")
def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    frontend = (get_settings().regret_public_url or "").rstrip("/") or "http://127.0.0.1:5173"
    if error:
        return RedirectResponse(f"{frontend}/app/settings/broker?alpaca=denied")
    if not code or not state:
        return RedirectResponse(f"{frontend}/app/settings/broker?alpaca=invalid")
    try:
        connections.complete_oauth(db, code=code, state=state)
    except ValidationFailed:
        return RedirectResponse(f"{frontend}/app/settings/broker?alpaca=invalid")
    except IntegrationUnavailable:
        return RedirectResponse(f"{frontend}/app/settings/broker?alpaca=failed")
    return RedirectResponse(f"{frontend}/app/settings/broker?alpaca=connected")


@router.post("/keys")
def connect_keys(
    body: KeyConnectBody,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    conn = connections.connect_with_api_keys(
        db,
        user_id=user.id,
        environment=body.environment,
        api_key_id=body.api_key_id,
        api_secret=body.api_secret,
    )
    return {"connected": True, "connection": connections.public_connection(conn)}


@router.get("/book")
def book(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Retrieve the user's real Alpaca book. Never invents an account."""
    return account_service.get_book(db, user.id)


@router.delete("/connection")
def disconnect(
    environment: str = Query(default="paper"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    connections.disconnect(db, user.id, environment)
    return {"disconnected": True}
