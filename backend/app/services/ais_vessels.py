"""Persists `AisMessage` events as "last known contact per MMSI" and
queries them back out. Same EventBus-subscriber shape as
`adsb_aircraft.py`.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.events import Event
from app.db.models.ais_vessel import AisVessel
from app.db.session import get_session_factory

DEFAULT_VESSEL_MINUTES = 60


async def persist_ais_vessel(event: Event) -> None:
    mmsi = event.data.get("mmsi")
    message_type = event.data.get("message_type")
    if mmsi is None or message_type is None:
        return
    # Only present for Class A position reports (message type 1/2/3 --
    # see decoders/ais_position.py); most message types never carry one.
    latitude = event.data.get("latitude")
    longitude = event.data.get("longitude")

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(AisVessel).where(AisVessel.receiver_id == event.source, AisVessel.mmsi == mmsi)
        )
        vessel = result.scalar_one_or_none()
        if vessel is None:
            vessel = AisVessel(
                receiver_id=event.source,
                mmsi=mmsi,
                last_message_type=message_type,
                message_count=1,
                first_seen_at=event.timestamp,
                last_seen_at=event.timestamp,
                latitude=latitude,
                longitude=longitude,
            )
            db.add(vessel)
        else:
            vessel.last_message_type = message_type
            vessel.message_count += 1
            vessel.last_seen_at = event.timestamp
            # Only overwrite a known position with another known
            # position -- a message without one (e.g. static/voyage
            # data) shouldn't blank out the vessel's last real fix.
            if latitude is not None and longitude is not None:
                vessel.latitude = latitude
                vessel.longitude = longitude
        await db.commit()


async def list_vessels(
    receiver_id: str | None = None, minutes: int = DEFAULT_VESSEL_MINUTES
) -> list[AisVessel]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    session_factory = get_session_factory()
    async with session_factory() as db:
        query = select(AisVessel).where(AisVessel.last_seen_at >= since)
        if receiver_id is not None:
            query = query.where(AisVessel.receiver_id == receiver_id)
        result = await db.execute(query.order_by(AisVessel.last_seen_at.desc()))
        return list(result.scalars().all())
