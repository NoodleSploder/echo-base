"""Add margin_db column to receiver_profiles.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("receiver_profiles", sa.Column("margin_db", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("receiver_profiles", "margin_db")
