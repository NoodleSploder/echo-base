from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings
from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_session_token, verify_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import CurrentUser, LoginRequest, LoginResponse
from app.schemas.common import ok

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if user is None or user.disabled or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("Invalid username or password.")

    token = create_session_token(subject=user.id, role=user.role.value, settings=settings)
    response.set_cookie(
        settings.security.cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.security.access_token_expire_minutes * 60,
    )
    return ok(
        LoginResponse(
            username=user.username,
            role=user.role.value,
            must_change_password=user.must_change_password,
        ).model_dump()
    )


@router.post("/logout")
async def logout(response: Response, settings: Settings = Depends(get_settings)) -> dict:
    response.delete_cookie(settings.security.cookie_name)
    return ok({"message": "Logged out."})


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict:
    current = CurrentUser(id=user.id, username=user.username, role=user.role.value, disabled=user.disabled)
    return ok(current.model_dump())
