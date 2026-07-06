"""Persisted signal detections (Phase 4: signal history).

Distinct from the in-memory `EventBus` history (`GET /api/events`,
bounded to the last 500 events across *all* event types and lost on
restart): this is specifically `SignalDetected` events, kept in the
database so a receiver's detection history survives a restart and can
be queried by time range/receiver rather than just "the last N events
of any kind."
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SignalDetectionRecord(Base):
    __tablename__ = "signal_detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    frequency_hz: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency_offset_hz: Mapped[float] = mapped_column(Float, nullable=False)
    power_db: Mapped[float] = mapped_column(Float, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
