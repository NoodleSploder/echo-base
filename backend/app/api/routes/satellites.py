"""Satellite pass prediction (Phase 9)."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import (
    get_current_user,
    get_receiver_service,
    get_scheduled_recording_service,
    require_role,
)
from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models.user import User, UserRole
from app.schemas.common import ok
from app.services.receiver_service import ReceiverService
from app.services.satellite_passes import InvalidTleError, find_passes
from app.services.scheduled_recording import ScheduledRecordingService

router = APIRouter(prefix="/api/satellites", tags=["satellites"])
require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


class PassPredictionRequest(BaseModel):
    tle_line1: str
    tle_line2: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0
    hours: float = 24.0
    min_elevation_deg: float = 10.0


def _find_passes(payload: PassPredictionRequest) -> list:
    try:
        return find_passes(
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


@router.post("/passes")
async def predict_passes(
    payload: PassPredictionRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Caller supplies a current TLE (e.g. fetched from Celestrak) --
    this endpoint doesn't fetch, cache, or ship any TLE data of its
    own, since a bundled one would go stale (see
    `satellite_passes.py`'s docstring)."""
    passes = _find_passes(payload)
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


class ScheduleNextPassRequest(PassPredictionRequest):
    mode: str = "fm"
    # Tuned immediately (not at AOS) so the receiver is already on the
    # satellite's downlink frequency by the time the scheduled
    # recording fires -- ScheduledRecordingService itself doesn't tune,
    # it just records whatever the receiver is on at start time.
    frequency_hz: int | None = None


@router.post("/{receiver_id}/schedule-next-pass")
async def schedule_next_pass_recording(
    receiver_id: str,
    payload: ScheduleNextPassRequest,
    receiver_service: ReceiverService = Depends(get_receiver_service),
    scheduled_recording_service: ScheduledRecordingService = Depends(get_scheduled_recording_service),
    _: User = Depends(require_operator),
) -> dict:
    """Finds the next pass within `hours` and schedules a recording
    covering it exactly (AOS -> LOS), reusing `ScheduledRecordingService`
    rather than a separate scheduling mechanism."""
    passes = _find_passes(payload)
    if not passes:
        raise NotFoundError(f"No pass above {payload.min_elevation_deg}deg within the next {payload.hours}h.")
    next_pass = passes[0]

    if payload.frequency_hz is not None:
        await receiver_service.tune(receiver_id, payload.frequency_hz)

    duration_seconds = (next_pass.los_at - next_pass.aos_at).total_seconds()
    job = scheduled_recording_service.schedule(receiver_id, payload.mode, next_pass.aos_at, duration_seconds)

    return ok(
        {
            "job_id": job.id,
            "aos_at": next_pass.aos_at.isoformat(),
            "los_at": next_pass.los_at.isoformat(),
            "max_elevation_deg": round(next_pass.max_elevation_deg, 1),
            "duration_seconds": round(duration_seconds, 1),
        }
    )
