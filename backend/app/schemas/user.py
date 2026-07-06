from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.user import UserRole


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    role: UserRole = UserRole.OBSERVER


class UserUpdateRequest(BaseModel):
    role: UserRole | None = None
    disabled: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: UserRole
    disabled: bool
    must_change_password: bool
