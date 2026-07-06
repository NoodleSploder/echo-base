"""Add ais_vessels table.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ais_vessels",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receiver_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("mmsi", sa.Integer(), nullable=False, index=True),
        sa.Column("last_message_type", sa.Integer(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint("receiver_id", "mmsi", name="uq_ais_vessel_receiver_mmsi"),
    )


def downgrade() -> None:
    op.drop_table("ais_vessels")
