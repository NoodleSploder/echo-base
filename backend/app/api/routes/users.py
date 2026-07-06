from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.schemas.common import ok
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/api", tags=["users"])

require_admin = require_role(UserRole.ADMINISTRATOR)


@router.get("/roles")
async def list_roles(_: User = Depends(get_current_user)) -> dict:
    return ok([role.value for role in UserRole])


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()
    return ok([UserResponse.model_validate(u).model_dump() for u in users])


@router.post("/users", status_code=201)
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Username '{payload.username}' is already taken.", code="USERNAME_TAKEN")

    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return ok(UserResponse.model_validate(user).model_dump())


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User '{user_id}' does not exist.", code="USER_NOT_FOUND")

    if payload.role is not None:
        user.role = payload.role
    if payload.disabled is not None:
        user.disabled = payload.disabled
    if payload.password:
        user.hashed_password = hash_password(payload.password)
        user.must_change_password = False

    await db.commit()
    await db.refresh(user)
    return ok(UserResponse.model_validate(user).model_dump())


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    if user_id == current_user.id:
        raise ConflictError("You cannot delete your own account.", code="CANNOT_DELETE_SELF")

    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User '{user_id}' does not exist.", code="USER_NOT_FOUND")

    await db.delete(user)
    await db.commit()
    return ok({"message": "User deleted."})
