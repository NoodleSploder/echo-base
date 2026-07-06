"""Persisted AIS vessel sightings (last known contact per MMSI),
upserted on every `AisMessage` event -- same shape as
`adsb_aircraft.py`/`aprs_station.py`.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AisVessel(Base):
    __tablename__ = "ais_vessels"
    __table_args__ = (UniqueConstraint("receiver_id", "mmsi", name="uq_ais_vessel_receiver_mmsi"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    mmsi: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    last_message_type: Mapped[int] = mapped_column(Integer, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )
