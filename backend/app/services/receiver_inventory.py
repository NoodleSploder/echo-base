"""Persists "receivers ever seen" and queries them back out. Plain
upsert-on-seen, same shape as `aprs_stations.py` -- called from
`HotplugMonitor` on every discovery poll (both the initial silent
seed and every subsequent `check_once()`), not tied to any particular
event type.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.db.models.receiver_inventory import ReceiverInventoryRecord
from app.db.session import get_session_factory
from app.plugins.receiver import ReceiverDescriptor


async def upsert_seen(descriptor: ReceiverDescriptor, seen_at: datetime | None = None) -> None:
    seen_at = seen_at or datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(ReceiverInventoryRecord).where(
                ReceiverInventoryRecord.receiver_id == descriptor.id
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = ReceiverInventoryRecord(
                receiver_id=descriptor.id,
                name=descriptor.name,
                driver=descriptor.driver,
                serial=descriptor.serial,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
            )
            db.add(record)
        else:
            record.name = descriptor.name
            record.driver = descriptor.driver
            record.serial = descriptor.serial
            record.last_seen_at = seen_at
        await db.commit()


async def list_inventory() -> list[ReceiverInventoryRecord]:
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(ReceiverInventoryRecord).order_by(ReceiverInventoryRecord.last_seen_at.desc())
        )
        return list(result.scalars().all())


async def set_location(
    receiver_id: str, latitude: float, longitude: float, site_name: str | None
) -> ReceiverInventoryRecord:
    """Set (or clear, if this receiver_id has never been seen) a
    receiver's physical site location -- deliberately operator-set, not
    inferred from anything (no GPS on a plain RTL-SDR dongle). Requires
    the receiver to have been seen at least once (i.e. exist in
    inventory already) since a location on its own is meaningless."""
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(ReceiverInventoryRecord).where(ReceiverInventoryRecord.receiver_id == receiver_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise NotFoundError(f"Receiver '{receiver_id}' has never been seen -- cannot set its location.")
        record.latitude = latitude
        record.longitude = longitude
        record.site_name = site_name
        await db.commit()
        await db.refresh(record)
        return record
