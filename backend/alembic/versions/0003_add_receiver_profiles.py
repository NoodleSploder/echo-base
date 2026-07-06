"""Add receiver_profiles table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "receiver_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("frequency_hz", sa.BigInteger(), nullable=False),
        sa.Column("sample_rate_hz", sa.BigInteger(), nullable=True),
        sa.Column("bandwidth_hz", sa.BigInteger(), nullable=True),
        sa.Column("gain", sa.String(length=32), nullable=True),
        sa.Column("decoder", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("receiver_profiles")
