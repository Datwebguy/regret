from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class BrokerOrder(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    approval_id: Mapped[str] = mapped_column(String(36), ForeignKey("approvals.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id"), index=True)
    intent_id: Mapped[str] = mapped_column(String(36), ForeignKey("trade_intents.id"), index=True)
    environment: Mapped[str] = mapped_column(String(16), nullable=False)
    alpaca_order_id: Mapped[str] = mapped_column(String(64), default="", nullable=False, index=True)
    client_order_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    alpaca_request_id: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="submitted")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_response_json: Mapped[str] = mapped_column(Text, default="", nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
