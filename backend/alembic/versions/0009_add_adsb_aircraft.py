"""Add adsb_aircraft table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "adsb_aircraft",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receiver_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("icao", sa.String(length=6), nullable=False, index=True),
        sa.Column("last_type_code", sa.Integer(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint("receiver_id", "icao", name="uq_adsb_aircraft_receiver_icao"),
    )


def downgrade() -> None:
    op.drop_table("adsb_aircraft")
