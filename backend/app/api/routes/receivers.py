from __future__ import annotations

from dataclasses import asdict, replace

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_receiver_service, get_stream_service, require_role
from app.db.models.user import User, UserRole
from app.plugins.receiver import ReceiverStatus
from app.schemas.common import ok
from app.schemas.receiver import (
    BandwidthRequest,
    GainRequest,
    ReceiverDescriptorSchema,
    ReceiverStatusSchema,
    SampleRateRequest,
    TuneRequest,
)
from app.services.receiver_service import ReceiverService
from app.services.stream_service import StreamService

router = APIRouter(prefix="/api/receivers", tags=["receivers"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


def _status_response(status: ReceiverStatus, receiver_id: str, stream_service: StreamService) -> dict:
    # `status.state` is a manual flag toggled by start()/stop() -- it
    # doesn't know whether a spectrum/audio subscriber has actually
    # triggered a live IQ capture. Report "streaming" whenever one has,
    # even if the receiver was never explicitly start()ed, so the UI
    # reflects real hardware activity rather than just the button state.
    if status.state == "idle" and stream_service.is_active(receiver_id):
        status = replace(status, state="streaming")
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.get("")
async def list_receivers(
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(get_current_user),
) -> dict:
    receivers = await service.list_receivers()
    return ok([ReceiverDescriptorSchema(**asdict(r)).model_dump() for r in receivers])


@router.post("/discover")
async def discover_receivers(
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    receivers = await service.discover()
    return ok([ReceiverDescriptorSchema(**asdict(r)).model_dump() for r in receivers])


@router.get("/{receiver_id}")
async def get_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(get_current_user),
) -> dict:
    status = await service.status(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/start")
async def start_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.start(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/stop")
async def stop_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.stop(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/tune")
async def tune_receiver(
    receiver_id: str,
    payload: TuneRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.tune(receiver_id, payload.frequency)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/gain")
async def set_gain(
    receiver_id: str,
    payload: GainRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_gain(receiver_id, payload.gain)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/bandwidth")
async def set_bandwidth(
    receiver_id: str,
    payload: BandwidthRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_bandwidth(receiver_id, payload.bandwidth)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/sample-rate")
async def set_sample_rate(
    receiver_id: str,
    payload: SampleRateRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_sample_rate(receiver_id, payload.sample_rate)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/aprs/start")
async def start_aprs_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    # Confirms the receiver exists (raises ReceiverNotFoundError otherwise)
    # before claiming hardware for it.
    await service.status(receiver_id)
    await stream_service.enable_aprs(receiver_id)
    return ok({"message": "APRS decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/aprs/stop")
async def stop_aprs_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_aprs(receiver_id)
    return ok({"message": "APRS decoding disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/same/start")
async def start_same_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await service.status(receiver_id)
    await stream_service.enable_same(receiver_id)
    return ok({"message": "SAME decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/same/stop")
async def stop_same_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_same(receiver_id)
    return ok({"message": "SAME decoding disabled.", "receiver_id": receiver_id})
