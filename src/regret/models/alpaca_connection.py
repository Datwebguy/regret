from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from regret.db.base import Base, TimestampMixin


class AlpacaConnection(Base, TimestampMixin):
    __tablename__ = "alpaca_connections"
    __table_args__ = (UniqueConstraint("user_id", "environment", name="uq_alpaca_user_env"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="paper")
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    alpaca_account_id: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    alpaca_account_number: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False)
    scopes: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="", nullable=False)
