"""Satellite pass prediction (Phase 9)."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import ValidationAppError
from app.db.models.user import User
from app.schemas.common import ok
from app.services.satellite_passes import InvalidTleError, find_passes

router = APIRouter(prefix="/api/satellites", tags=["satellites"])


class PassPredictionRequest(BaseModel):
    tle_line1: str
    tle_line2: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0
    hours: float = 24.0
    min_elevation_deg: float = 10.0


@router.post("/passes")
async def predict_passes(
    payload: PassPredictionRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Caller supplies a current TLE (e.g. fetched from Celestrak) --
    this endpoint doesn't fetch, cache, or ship any TLE data of its
    own, since a bundled one would go stale (see
    `satellite_passes.py`'s docstring)."""
    try:
        passes = find_passes(
            payload.tle_line1,
            payload.tle_line2,
            payload.latitude_deg,
            payload.longitude_deg,
            payload.elevation_m,
            datetime.now(UTC),
            payload.hours,
            payload.min_elevation_deg,
        )
    except (InvalidTleError, ValueError, IndexError) as exc:
        raise ValidationAppError(f"Invalid TLE: {exc}") from exc

    return ok(
        [
            {
                "aos_at": p.aos_at.isoformat(),
                "los_at": p.los_at.isoformat(),
                "max_elevation_deg": round(p.max_elevation_deg, 1),
            }
            for p in passes
        ]
    )
