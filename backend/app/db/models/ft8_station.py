"""Persisted FT8 station sightings (last known contact per
`call_de`), upserted on every decoded `Ft8Message` event -- same "last
known position, not full track history" shape as `aprs_station.py`.

Position is the *grid square's centroid*, not a real GPS fix -- FT8
only ever conveys a 4-character Maidenhead locator (roughly
150km x 300km at mid-latitudes), and only when the decoded message
happens to carry a grid rather than a signal report or token
(see `decoders/ft8_message.py`).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Ft8Station(Base):
    __tablename__ = "ft8_stations"
    __table_args__ = (UniqueConstraint("receiver_id", "callsign", name="uq_ft8_station_receiver_callsign"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # call_de -- the callsign of the station actually reporting itself,
    # not call_to (which is often "CQ" or a directed-call token, not a
    # real station identity worth tracking a position for).
    callsign: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    grid: Mapped[str | None] = mapped_column(String(8), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_message: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency_offset_hz: Mapped[float] = mapped_column(Float, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_heard_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_heard_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )
