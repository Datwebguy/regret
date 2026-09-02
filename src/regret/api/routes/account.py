from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.preferences import UserPreference
from regret.models.user import User
from regret.config import get_settings
from regret.services import account as account_service

router = APIRouter(prefix="/api", tags=["account"])


class PreferencePatch(BaseModel):
    default_environment: str | None = None
    monitoring_enabled: bool | None = None
    allow_analysis_without_stop: bool | None = None
    display_name: str | None = None


def _prefs(db: Session, user: User) -> UserPreference:
    row = db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))
    if row is None:
        row = UserPreference(user_id=user.id)
        db.add(row)
        db.flush()
    return row


def _public_prefs(user: User, row: UserPreference) -> dict:
    return {
        "email": user.email,
        "display_name": user.display_name,
        "default_environment": row.default_environment,
        "monitoring_enabled": row.monitoring_enabled,
        "allow_analysis_without_stop": row.allow_analysis_without_stop,
        "live_trading_enabled": get_settings().regret_live_trading_enabled,
    }


@router.get("/preferences")
def get_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return _public_prefs(user, _prefs(db, user))


@router.patch("/preferences")
def patch_preferences(
    body: PreferencePatch,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _prefs(db, user)
    if body.default_environment == "paper":
        row.default_environment = "paper"
    elif body.default_environment == "live":
        if not get_settings().regret_live_trading_enabled:
            row.default_environment = "paper"
        else:
            row.default_environment = "live"
    if body.monitoring_enabled is not None:
        row.monitoring_enabled = body.monitoring_enabled
    if body.allow_analysis_without_stop is not None:
        row.allow_analysis_without_stop = body.allow_analysis_without_stop
    if body.display_name is not None:
        user.display_name = body.display_name.strip()[:120]
    return _public_prefs(user, row)


@router.get("/account")
def account(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return account_service.get_book(db, user.id)


@router.get("/portfolio")
def portfolio(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return account_service.get_book(db, user.id)


@router.get("/positions")
def positions(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return account_service.get_positions(db, user.id)


@router.get("/broker-orders")
def broker_orders(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return account_service.get_orders(db, user.id)
