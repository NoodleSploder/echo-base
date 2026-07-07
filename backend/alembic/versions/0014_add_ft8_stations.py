"""Add ft8_stations table.

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ft8_stations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receiver_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("callsign", sa.String(length=16), nullable=False, index=True),
        sa.Column("grid", sa.String(length=8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("last_message", sa.String(length=64), nullable=False),
        sa.Column("frequency_offset_hz", sa.Float(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("first_heard_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heard_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint("receiver_id", "callsign", name="uq_ft8_station_receiver_callsign"),
    )


def downgrade() -> None:
    op.drop_table("ft8_stations")
