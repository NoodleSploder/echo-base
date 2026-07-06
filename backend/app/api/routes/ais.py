"""Read access to persisted AIS vessel sightings."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.common import ok
from app.services.ais_vessels import DEFAULT_VESSEL_MINUTES, list_vessels

router = APIRouter(prefix="/api/ais", tags=["ais"])


@router.get("/vessels")
async def list_ais_vessels(
    receiver_id: str | None = None,
    minutes: int = DEFAULT_VESSEL_MINUTES,
    _: User = Depends(get_current_user),
) -> dict:
    vessels = await list_vessels(receiver_id=receiver_id, minutes=minutes)
    return ok(
        [
            {
                "receiver_id": v.receiver_id,
                "mmsi": v.mmsi,
                "last_message_type": v.last_message_type,
                "message_count": v.message_count,
                "first_seen_at": v.first_seen_at.isoformat(),
                "last_seen_at": v.last_seen_at.isoformat(),
                "latitude": v.latitude,
                "longitude": v.longitude,
            }
            for v in vessels
        ]
    )
