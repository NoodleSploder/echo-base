"""Add aprs_stations table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "aprs_stations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receiver_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("callsign", sa.String(length=16), nullable=False, index=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("symbol", sa.String(length=4), nullable=True),
        sa.Column("last_info", sa.String(length=256), nullable=False),
        sa.Column("first_heard_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heard_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint("receiver_id", "callsign", name="uq_aprs_station_receiver_callsign"),
    )


def downgrade() -> None:
    op.drop_table("aprs_stations")
