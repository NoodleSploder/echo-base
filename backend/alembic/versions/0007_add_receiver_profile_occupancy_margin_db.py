"""Add occupancy_margin_db column to receiver_profiles.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("receiver_profiles", sa.Column("occupancy_margin_db", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("receiver_profiles", "occupancy_margin_db")
