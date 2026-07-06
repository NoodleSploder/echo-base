"""Password hashing and session token helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


class TokenError(Exception):
    """Raised when a session token is missing, malformed, or expired."""


def create_session_token(*, subject: str, role: str, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.security.access_token_expire_minutes),
        "type": "session",
    }
    return jwt.encode(payload, settings.security.secret_key, algorithm=settings.security.algorithm)


def decode_session_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
