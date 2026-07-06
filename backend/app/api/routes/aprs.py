"""Read access to persisted APRS station positions (Phase 9: mapping groundwork)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.common import ok
from app.services.aprs_stations import DEFAULT_STATION_MINUTES, query_aprs_stations

router = APIRouter(prefix="/api/aprs", tags=["aprs"])


@router.get("/stations")
async def list_aprs_stations(
    receiver_id: str | None = None,
    minutes: int = DEFAULT_STATION_MINUTES,
    _: User = Depends(get_current_user),
) -> dict:
    stations = await query_aprs_stations(receiver_id=receiver_id, minutes=minutes)
    return ok(
        [
            {
                "receiver_id": s.receiver_id,
                "callsign": s.callsign,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "symbol": s.symbol,
                "last_info": s.last_info,
                "first_heard_at": s.first_heard_at.isoformat(),
                "last_heard_at": s.last_heard_at.isoformat(),
            }
            for s in stations
        ]
    )
