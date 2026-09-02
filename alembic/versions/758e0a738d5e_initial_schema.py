"""initial schema

Revision ID: 758e0a738d5e
Revises:
Create Date: 2026-08-12 13:53:21.941771
"""
from typing import Sequence, Union

from alembic import op

from regret.db.base import Base
import regret.models  # noqa: F401

revision: str = "758e0a738d5e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
