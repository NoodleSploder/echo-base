from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_receiver_service, require_role
from app.db.models.user import User, UserRole
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

router = APIRouter(prefix="/api/receivers", tags=["receivers"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


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
    _: User = Depends(get_current_user),
) -> dict:
    status = await service.status(receiver_id)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/start")
async def start_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.start(receiver_id)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/stop")
async def stop_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.stop(receiver_id)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/tune")
async def tune_receiver(
    receiver_id: str,
    payload: TuneRequest,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.tune(receiver_id, payload.frequency)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/gain")
async def set_gain(
    receiver_id: str,
    payload: GainRequest,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_gain(receiver_id, payload.gain)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/bandwidth")
async def set_bandwidth(
    receiver_id: str,
    payload: BandwidthRequest,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_bandwidth(receiver_id, payload.bandwidth)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.post("/{receiver_id}/sample-rate")
async def set_sample_rate(
    receiver_id: str,
    payload: SampleRateRequest,
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_sample_rate(receiver_id, payload.sample_rate)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())
