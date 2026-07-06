"""Add latitude/longitude columns to adsb_aircraft.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-06

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("adsb_aircraft", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("adsb_aircraft", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("adsb_aircraft", "longitude")
    op.drop_column("adsb_aircraft", "latitude")
