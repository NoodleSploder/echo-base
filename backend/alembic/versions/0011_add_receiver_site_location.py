"""Add site_name/latitude/longitude columns to receiver_inventory.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("receiver_inventory", sa.Column("site_name", sa.String(length=128), nullable=True))
    op.add_column("receiver_inventory", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("receiver_inventory", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("receiver_inventory", "longitude")
    op.drop_column("receiver_inventory", "latitude")
    op.drop_column("receiver_inventory", "site_name")
