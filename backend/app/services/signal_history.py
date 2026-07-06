"""Persists `SignalDetected` events to the database (Phase 4: signal
history) and queries them back out.

A plain `EventBus` subscriber rather than something StreamService calls
directly -- StreamService already has no idea whether anything is
listening to the events it emits (that's the point of the event bus),
so persistence is just another subscriber, exactly like the WebSocket
fan-out `ConnectionManager` already is.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.events import Event
from app.db.models.signal_detection import SignalDetectionRecord
from app.db.session import get_session_factory

DEFAULT_HISTORY_LIMIT = 200
DEFAULT_HISTORY_MINUTES = 60


async def persist_signal_detected(event: Event) -> None:
    record = SignalDetectionRecord(
        receiver_id=event.source,
        frequency_hz=event.data.get("frequency_hz"),
        frequency_offset_hz=event.data["frequency_offset_hz"],
        power_db=event.data["power_db"],
        detected_at=event.timestamp,
    )
    session_factory = get_session_factory()
    async with session_factory() as db:
        db.add(record)
        await db.commit()


async def query_signal_history(
    receiver_id: str, minutes: int = DEFAULT_HISTORY_MINUTES, limit: int = DEFAULT_HISTORY_LIMIT
) -> list[SignalDetectionRecord]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(SignalDetectionRecord)
            .where(
                SignalDetectionRecord.receiver_id == receiver_id,
                SignalDetectionRecord.detected_at >= since,
            )
            .order_by(SignalDetectionRecord.detected_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
