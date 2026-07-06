"""Persisted APRS station positions (Phase 9: mapping groundwork).

One row per (receiver_id, callsign), upserted on every position-
bearing `AprsPacket` event -- "where's the most recent place we heard
this station report itself from", not a full track history. A real
position history log (for a future actual track/breadcrumb trail) is
a bigger addition than this slice; see the diary entry for why this
starts with "last known position" only, same reasoning as
`SignalDetectionRecord` starting without retention/pruning.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AprsStation(Base):
    __tablename__ = "aprs_stations"
    __table_args__ = (UniqueConstraint("receiver_id", "callsign", name="uq_aprs_station_receiver_callsign"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    callsign: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(4), nullable=True)
    last_info: Mapped[str] = mapped_column(String(256), nullable=False)
    first_heard_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_heard_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )
