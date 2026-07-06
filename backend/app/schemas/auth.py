from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str
    must_change_password: bool = False


class CurrentUser(BaseModel):
    id: str
    username: str
    role: str
    disabled: bool
