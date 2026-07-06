"""Saved receiver tuning presets (frequency/gain/bandwidth/decoder)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ReceiverProfile(Base):
    __tablename__ = "receiver_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    frequency_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sample_rate_hz: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bandwidth_hz: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    gain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decoder: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # dB above the noise floor (see signal_detection.py's docstring for
    # why this is relative, not absolute) -- if set, applying this
    # profile also auto-enables signal detection at this margin, same
    # "decoder" auto-enable pattern applied to APRS/SAME.
    margin_db: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
