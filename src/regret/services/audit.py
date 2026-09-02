from __future__ import annotations

from sqlalchemy.orm import Session

from regret.models.audit import AuditLog


def record(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    entity_type: str = "",
    entity_id: str = "",
    symbol: str = "",
    decision_id: str = "",
    order_id: str = "",
    status: str = "",
    request_id: str = "",
    detail: str = "",
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            symbol=symbol,
            decision_id=decision_id,
            order_id=order_id,
            status=status,
            request_id=request_id,
            detail=detail,
        )
    )
