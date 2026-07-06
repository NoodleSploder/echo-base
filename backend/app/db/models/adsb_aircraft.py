"""Persisted ADS-B aircraft sightings (last known contact per ICAO
address), upserted on every `AdsbMessage` event -- same shape as
`aprs_station.py`: "who's currently on the map", not a full message
log.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AdsbAircraft(Base):
    __tablename__ = "adsb_aircraft"
    __table_args__ = (UniqueConstraint("receiver_id", "icao", name="uq_adsb_aircraft_receiver_icao"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    icao: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    last_type_code: Mapped[int] = mapped_column(Integer, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # None until a real even/odd CPR frame pair has been decoded for
    # this aircraft (see decoders/adsb_position.py) -- most type-code-1
    # (identification-only) sightings never get one.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )
