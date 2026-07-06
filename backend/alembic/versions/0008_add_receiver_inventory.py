"""Add receiver_inventory table.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "receiver_inventory",
        sa.Column("receiver_id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("driver", sa.String(length=64), nullable=False),
        sa.Column("serial", sa.String(length=64), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("receiver_inventory")
