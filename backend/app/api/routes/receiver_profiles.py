"""CRUD for saved receiver tuning presets, plus applying one to a live receiver."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_receiver_service, require_role
from app.core.exceptions import NotFoundError
from app.db.models.receiver_profile import ReceiverProfile
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.schemas.common import ok
from app.schemas.receiver import ReceiverStatusSchema
from app.schemas.receiver_profile import (
    ReceiverProfileCreate,
    ReceiverProfileSchema,
    ReceiverProfileUpdate,
)
from app.services.receiver_service import ReceiverService

router = APIRouter(prefix="/api/receiver-profiles", tags=["receiver-profiles"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


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
) -> dict:
    profile = await _get_owned_profile(profile_id, user, db)
    await service.tune(receiver_id, profile.frequency_hz)
    if profile.gain is not None:
        await service.set_gain(receiver_id, profile.gain)
    status = await service.status(receiver_id)
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())
