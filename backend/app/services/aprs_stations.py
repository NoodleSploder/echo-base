"""Persists position-bearing `AprsPacket` events as "last known
position per station" (Phase 9: mapping groundwork) and queries them
back out.

Same EventBus-subscriber shape as `signal_history.py` -- StreamService
has no idea anything is listening to the events it emits, persistence
is just another subscriber.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.events import Event
from app.db.models.aprs_station import AprsStation
from app.db.session import get_session_factory

DEFAULT_STATION_MINUTES = 1440  # 24h -- APRS stations often beacon only every 10-30 minutes


async def persist_aprs_station(event: Event) -> None:
    latitude = event.data.get("latitude")
    longitude = event.data.get("longitude")
    if latitude is None or longitude is None:
        return  # no position in this packet (e.g. a message/status frame) -- nothing to track

    callsign = str(event.data.get("source", ""))
    if not callsign:
        return

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(AprsStation).where(
                AprsStation.receiver_id == event.source, AprsStation.callsign == callsign
            )
        )
        station = result.scalar_one_or_none()
        if station is None:
            station = AprsStation(
                receiver_id=event.source,
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol=event.data.get("symbol"),
                last_info=str(event.data.get("info", ""))[:256],
                first_heard_at=event.timestamp,
                last_heard_at=event.timestamp,
            )
            db.add(station)
        else:
            station.latitude = latitude
            station.longitude = longitude
            station.symbol = event.data.get("symbol")
            station.last_info = str(event.data.get("info", ""))[:256]
            station.last_heard_at = event.timestamp
        await db.commit()


async def query_aprs_stations(
    receiver_id: str | None = None, minutes: int = DEFAULT_STATION_MINUTES
) -> list[AprsStation]:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    session_factory = get_session_factory()
    async with session_factory() as db:
        query = select(AprsStation).where(AprsStation.last_heard_at >= since)
        if receiver_id is not None:
            query = query.where(AprsStation.receiver_id == receiver_id)
        result = await db.execute(query.order_by(AprsStation.last_heard_at.desc()))
        return list(result.scalars().all())
