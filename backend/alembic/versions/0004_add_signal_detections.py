"""Add signal_detections table.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "signal_detections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("receiver_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("frequency_hz", sa.Float(), nullable=True),
        sa.Column("frequency_offset_hz", sa.Float(), nullable=False),
        sa.Column("power_db", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("signal_detections")
