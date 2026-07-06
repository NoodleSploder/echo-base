"""CRUD for saved receiver tuning presets, plus applying one to a live receiver."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_receiver_service, get_stream_service, require_role
from app.api.routes.receivers import _status_response
from app.core.exceptions import NotFoundError
from app.db.models.receiver_profile import ReceiverProfile
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.schemas.common import ok
from app.schemas.receiver_profile import (
    ReceiverProfileCreate,
    ReceiverProfileSchema,
    ReceiverProfileUpdate,
)
from app.services.receiver_service import ReceiverService
from app.services.stream_service import StreamService
from app.services.suggested_profiles import SUGGESTED_PROFILES

router = APIRouter(prefix="/api/receiver-profiles", tags=["receiver-profiles"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


@router.get("/suggested")
async def list_suggested_profiles(_: User = Depends(get_current_user)) -> dict:
    """Static built-in band presets, not stored per-user -- see
    `suggested_profiles.py` for why these aren't database rows."""
    return ok(
        [
            {
                "id": p.id,
                "name": p.name,
                "frequency_hz": p.frequency_hz,
                "gain": p.gain,
                "decoder": p.decoder,
                "description": p.description,
            }
            for p in SUGGESTED_PROFILES
        ]
    )


async def _get_owned_profile(profile_id: str, user: User, db: AsyncSession) -> ReceiverProfile:
    result = await db.execute(
        select(ReceiverProfile).where(ReceiverProfile.id == profile_id, ReceiverProfile.owner_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Receiver profile '{profile_id}' not found.")
    return profile


@router.get("")
async def list_profiles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ReceiverProfile).where(ReceiverProfile.owner_id == user.id).order_by(ReceiverProfile.name)
    )
    profiles = result.scalars().all()
    return ok([ReceiverProfileSchema.model_validate(p).model_dump() for p in profiles])


@router.post("")
async def create_profile(
    payload: ReceiverProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = ReceiverProfile(owner_id=user.id, **payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return ok(ReceiverProfileSchema.model_validate(profile).model_dump())


@router.put("/{profile_id}")
async def update_profile(
    profile_id: str,
    payload: ReceiverProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await _get_owned_profile(profile_id, user, db)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return ok(ReceiverProfileSchema.model_validate(profile).model_dump())


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _get_owned_profile(profile_id, user, db)
    await db.execute(
        delete(ReceiverProfile).where(ReceiverProfile.id == profile_id, ReceiverProfile.owner_id == user.id)
    )
    await db.commit()
    return ok({"message": "Profile deleted."})


@router.post("/{profile_id}/apply/{receiver_id}")
async def apply_profile(
    profile_id: str,
    receiver_id: str,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
) -> dict:
    profile = await _get_owned_profile(profile_id, user, db)
    await service.tune(receiver_id, profile.frequency_hz)
    if profile.gain is not None:
        await service.set_gain(receiver_id, profile.gain)
    # Auto-enables the profile's suggested decoder (see
    # suggested_profiles.py) so "Add + Apply" is a genuine one-click
    # path to a decoding receiver, not just a retuned one. Only ever
    # turns a decoder *on* -- switching profiles never turns a
    # currently-running decoder off, since that's the same "don't
    # surprise-stop something the user started on purpose" reasoning
    # as everywhere else decoders are controlled explicitly.
    if profile.decoder == "aprs":
        await stream_service.enable_aprs(receiver_id)
    elif profile.decoder == "same":
        await stream_service.enable_same(receiver_id)
    # Same auto-enable-only-on reasoning as the decoder above, extended
    # to signal detection now that a profile has a natural place to
    # carry a margin_db (it didn't when decoder auto-enable first shipped).
    if profile.margin_db is not None:
        await stream_service.enable_signal_detection(receiver_id, profile.margin_db, profile.frequency_hz)
    if profile.occupancy_margin_db is not None:
        await stream_service.enable_occupancy(receiver_id, profile.occupancy_margin_db, profile.frequency_hz)
    status = await service.status(receiver_id)
    return _status_response(status, receiver_id, stream_service)
