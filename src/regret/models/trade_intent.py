from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class TradeIntent(Base, TimestampMixin):
    __tablename__ = "trade_intents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trade_intents.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    notional: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    order_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    limit_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    stop_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    target_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    parse_source: Mapped[str] = mapped_column(String(32), default="structured", nullable=False)
    parse_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
