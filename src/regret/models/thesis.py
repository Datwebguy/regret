from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class TradeThesis(Base, TimestampMixin):
    __tablename__ = "trade_theses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    entry: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    invalidation: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    target: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    risk_reward: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rules_passed_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    rules_failed_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    market_conditions_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    state: Mapped[str] = mapped_column(String(32), default="intact", nullable=False)
    last_review_json: Mapped[str] = mapped_column(Text, default="", nullable=False)
