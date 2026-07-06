"""Recording start/stop (per receiver), the recordings library (global),
and playing a recorded `.iq` file back through the same spectrum/audio/
decoder pipeline live receivers use.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.deps import get_receiver_service, get_recording_service, get_stream_service, require_role
from app.core.exceptions import ValidationAppError
from app.db.models.user import User, UserRole
from app.schemas.common import ok
from app.services.receiver_service import ReceiverService
from app.services.recording_service import RecordingService
from app.services.stream_service import StreamService

router = APIRouter(tags=["recordings"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


class RecordingModeRequest(BaseModel):
    mode: str = "fm"


def _playback_id(filename: str) -> str:
    return f"playback:{filename}"


@router.get("/api/recordings")
async def list_recordings(
    recording_service: RecordingService = Depends(get_recording_service),
    _: User = Depends(require_operator),
) -> dict:
    return ok([asdict(r) for r in recording_service.list_recordings()])


@router.get("/api/recordings/{filename}/download")
async def download_recording(
    filename: str,
    recording_service: RecordingService = Depends(get_recording_service),
    _: User = Depends(require_operator),
) -> FileResponse:
    path = recording_service.path_for(filename)
    media_type = "audio/wav" if path.suffix == ".wav" else "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.delete("/api/recordings/{filename}")
async def delete_recording(
    filename: str,
    recording_service: RecordingService = Depends(get_recording_service),
    _: User = Depends(require_operator),
) -> dict:
    recording_service.delete(filename)
    return ok({"message": "Recording deleted.", "filename": filename})


@router.post("/api/receivers/{receiver_id}/recording/start")
async def start_recording(
    receiver_id: str,
    payload: RecordingModeRequest,
    service: ReceiverService = Depends(get_receiver_service),
    recording_service: RecordingService = Depends(get_recording_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.status(receiver_id)  # raises ReceiverNotFoundError if unknown
    info = await recording_service.start(receiver_id, payload.mode, status.frequency_hz)
    return ok(asdict(info))


@router.post("/api/receivers/{receiver_id}/recording/stop")
async def stop_recording(
    receiver_id: str,
    recording_service: RecordingService = Depends(get_recording_service),
    _: User = Depends(require_operator),
) -> dict:
    info = await recording_service.stop(receiver_id)
    return ok(asdict(info))


@router.post("/api/recordings/{filename}/playback/start")
async def start_playback(
    filename: str,
    recording_service: RecordingService = Depends(get_recording_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    path = recording_service.path_for(filename)  # raises RecordingNotFoundError if unknown
    if path.suffix != ".iq":
        raise ValidationAppError(
            "Only raw IQ recordings (.iq) can be played back through the spectrum/audio/decoder "
            "pipeline -- WAV recordings are already-demodulated audio."
        )
    sample_rate_hz = recording_service.sample_rate_for(filename)
    playback_id = _playback_id(filename)
    stream_service.register_playback(playback_id, path, sample_rate_hz)
    return ok({"playback_id": playback_id})


@router.post("/api/recordings/{filename}/playback/stop")
async def stop_playback(
    filename: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.unregister_playback(_playback_id(filename))
    return ok({"message": "Playback stopped."})
