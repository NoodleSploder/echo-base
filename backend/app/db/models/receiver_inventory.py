"""Persisted "receivers ever seen" (Phase 2: receiver inventory
persistence), distinct from `GET /api/receivers`'s live discovery,
which only ever shows what's currently attached.

One row per receiver_id, upserted every time `HotplugMonitor` sees it
in a discovery poll -- `first_seen_at` set once, `last_seen_at`
refreshed each time. A receiver unplugged mid-session stays in this
table with whatever `last_seen_at` it last had, so "what receivers has
this deployment ever had" survives both a receiver being unplugged and
a backend restart, neither of which the live-discovery-only view can
answer.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ReceiverInventoryRecord(Base):
    __tablename__ = "receiver_inventory"

    receiver_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver: Mapped[str] = mapped_column(String(64), nullable=False)
    serial: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )
    # Physical site location, set by an operator (never inferred) --
    # None until someone places this receiver on the map. Distinct from
    # everything else on this row, which is auto-populated by
    # HotplugMonitor on every discovery poll.
    site_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
