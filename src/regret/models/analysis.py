from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class Analysis(Base, TimestampMixin):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    intent_id: Mapped[str] = mapped_column(String(36), ForeignKey("trade_intents.id"), index=True)
    analysis_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    rule_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    data_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_source: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="paper")
    blocked_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id"), index=True)
    intent_id: Mapped[str] = mapped_column(String(36), ForeignKey("trade_intents.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    override: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preview_json: Mapped[str] = mapped_column(Text, nullable=False)
    client_order_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
