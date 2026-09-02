from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    intent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trade_intents.id"), nullable=True)
    analysis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("analyses.id"), nullable=True)
    approval_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("approvals.id"), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    thesis_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    user_action: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    override: Mapped[str] = mapped_column(String(8), default="NO", nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
