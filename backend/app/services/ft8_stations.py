"""Persists `Ft8Message` events as "last known contact per callsign"
and queries them back out. Same EventBus-subscriber shape as
`aprs_stations.py`/`adsb_aircraft.py`.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.events import Event
from app.db.models.ft8_station import Ft8Station
from app.db.session import get_session_factory

DEFAULT_STATION_MINUTES = 60


async def persist_ft8_station(event: Event) -> None:
    call_de = event.data.get("call_de")
    call_to = event.data.get("call_to")
    extra = event.data.get("extra")
    frequency_offset_hz = event.data.get("frequency_offset_hz")
    if call_de is None or call_to is None or extra is None or frequency_offset_hz is None:
        return
    # "<...>" is a real, valid decode (an unresolved hashed callsign --
    # see decoders/ft8_message.py) but not a real callsign to track a
    # position for.
    if call_de == "<...>":
        return

    grid = event.data.get("grid")
    latitude = event.data.get("latitude")
    longitude = event.data.get("longitude")
    last_message = f"{call_to} {call_de} {extra}"

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(Ft8Station).where(Ft8Station.receiver_id == event.source, Ft8Station.callsign == call_de)
        )
        station = result.scalar_one_or_none()
        if station is None:
            station = Ft8Station(
                receiver_id=event.source,
                callsign=call_de,
                grid=grid,
                latitude=latitude,
                longitude=longitude,
                last_message=last_message,
                frequency_offset_hz=frequency_offset_hz,
                message_count=1,
                first_heard_at=event.timestamp,
                last_heard_at=event.timestamp,
            )
            db.add(station)
        else:
            station.last_message = last_message
            station.frequency_offset_hz = frequency_offset_hz
            station.message_count += 1
            station.last_heard_at = event.timestamp
            # Only overwrite a known grid/position with another known
            # one -- a signal-report-only message (no grid) shouldn't
            # blank out this station's last known locator.
            if grid is not None:
                station.grid = grid
                station.latitude = latitude
                station.longitude = longitude
        await db.commit()


async def list_stations(
    receiver_id: str | None = None, minutes: int = DEFAULT_STATION_MINUTES
) -> list[Ft8Station]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    session_factory = get_session_factory()
    async with session_factory() as db:
        query = select(Ft8Station).where(Ft8Station.last_heard_at >= since)
        if receiver_id is not None:
            query = query.where(Ft8Station.receiver_id == receiver_id)
        result = await db.execute(query.order_by(Ft8Station.last_heard_at.desc()))
        return list(result.scalars().all())
