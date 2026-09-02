from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.user import User
from regret.services import journal, monitoring
from regret.services import orders as order_service

router = APIRouter(prefix="/api", tags=["orders"])


class PreviewBody(BaseModel):
    analysis_id: str


class ConfirmBody(BaseModel):
    approval_id: str
    confirm: bool = False
    accept_suggested_size: bool = False
    live_confirmation: str = ""


@router.post("/orders/preview")
def preview(body: PreviewBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return order_service.preview_order(db, user.id, body.analysis_id)


@router.post("/orders/confirm")
def confirm(body: ConfirmBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return order_service.confirm_order(
        db,
        user.id,
        approval_id=body.approval_id,
        confirm=body.confirm,
        accept_suggested_size=body.accept_suggested_size,
        live_confirmation=body.live_confirmation,
    )


@router.get("/orders")
def list_orders(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"orders": [order_service.serialize_order(o) for o in order_service.list_orders(db, user.id)]}


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return order_service.refresh_order(db, user.id, order_id)


@router.post("/orders/{order_id}/cancel")
def cancel(order_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return order_service.cancel_order(db, user.id, order_id)


@router.get("/journal")
def list_journal(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"entries": journal.list_entries(db, user.id)}


@router.get("/journal/{entry_id}")
def get_journal(entry_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return journal.get_entry(db, user.id, entry_id)


@router.get("/theses")
def theses(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"theses": monitoring.list_theses(db, user.id)}


@router.get("/monitor/{symbol}")
def monitor(symbol: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return monitoring.monitor_symbol(db, user.id, symbol)


@router.get("/alerts")
def alerts(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"alerts": monitoring.list_alerts(db, user.id)}


@router.get("/monitor")
def monitor_book(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return monitoring.broker_activity(db, user.id)
