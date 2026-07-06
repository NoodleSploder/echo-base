"""Read access to persisted ADS-B aircraft sightings."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.common import ok
from app.services.adsb_aircraft import DEFAULT_AIRCRAFT_MINUTES, list_aircraft

router = APIRouter(prefix="/api/adsb", tags=["adsb"])


@router.get("/aircraft")
async def list_adsb_aircraft(
    receiver_id: str | None = None,
    minutes: int = DEFAULT_AIRCRAFT_MINUTES,
    _: User = Depends(get_current_user),
) -> dict:
    aircraft = await list_aircraft(receiver_id=receiver_id, minutes=minutes)
    return ok(
        [
            {
                "receiver_id": a.receiver_id,
                "icao": a.icao,
                "last_type_code": a.last_type_code,
                "message_count": a.message_count,
                "first_seen_at": a.first_seen_at.isoformat(),
                "last_seen_at": a.last_seen_at.isoformat(),
                "latitude": a.latitude,
                "longitude": a.longitude,
            }
            for a in aircraft
        ]
    )
