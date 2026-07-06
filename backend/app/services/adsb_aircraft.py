"""Persists `AdsbMessage` events as "last known contact per ICAO
address" and queries them back out. Same EventBus-subscriber shape as
`aprs_stations.py`/`signal_history.py`.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.events import Event
from app.db.models.adsb_aircraft import AdsbAircraft
from app.db.session import get_session_factory

DEFAULT_AIRCRAFT_MINUTES = 60


async def persist_adsb_aircraft(event: Event) -> None:
    icao = event.data.get("icao")
    type_code = event.data.get("type_code")
    if icao is None or type_code is None:
        return

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(AdsbAircraft).where(AdsbAircraft.receiver_id == event.source, AdsbAircraft.icao == icao)
        )
        aircraft = result.scalar_one_or_none()
        if aircraft is None:
            aircraft = AdsbAircraft(
                receiver_id=event.source,
                icao=icao,
                last_type_code=type_code,
                message_count=1,
                first_seen_at=event.timestamp,
                last_seen_at=event.timestamp,
            )
            db.add(aircraft)
        else:
            aircraft.last_type_code = type_code
            aircraft.message_count += 1
            aircraft.last_seen_at = event.timestamp
        await db.commit()


async def list_aircraft(
    receiver_id: str | None = None, minutes: int = DEFAULT_AIRCRAFT_MINUTES
) -> list[AdsbAircraft]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    session_factory = get_session_factory()
    async with session_factory() as db:
        query = select(AdsbAircraft).where(AdsbAircraft.last_seen_at >= since)
        if receiver_id is not None:
            query = query.where(AdsbAircraft.receiver_id == receiver_id)
        result = await db.execute(query.order_by(AdsbAircraft.last_seen_at.desc()))
        return list(result.scalars().all())
