"""Read access to persisted FT8 station sightings."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.common import ok
from app.services.ft8_stations import DEFAULT_STATION_MINUTES, list_stations

router = APIRouter(prefix="/api/ft8", tags=["ft8"])


@router.get("/stations")
async def list_ft8_stations(
    receiver_id: str | None = None,
    minutes: int = DEFAULT_STATION_MINUTES,
    _: User = Depends(get_current_user),
) -> dict:
    stations = await list_stations(receiver_id=receiver_id, minutes=minutes)
    return ok(
        [
            {
                "receiver_id": s.receiver_id,
                "callsign": s.callsign,
                "grid": s.grid,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "last_message": s.last_message,
                "frequency_offset_hz": s.frequency_offset_hz,
                "message_count": s.message_count,
                "first_heard_at": s.first_heard_at.isoformat(),
                "last_heard_at": s.last_heard_at.isoformat(),
            }
            for s in stations
        ]
    )
