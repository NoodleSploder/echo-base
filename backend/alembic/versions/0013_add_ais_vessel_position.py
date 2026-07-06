"""Add latitude/longitude columns to ais_vessels.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ais_vessels", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("ais_vessels", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("ais_vessels", "longitude")
    op.drop_column("ais_vessels", "latitude")
