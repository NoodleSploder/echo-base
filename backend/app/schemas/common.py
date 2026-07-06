"""Standard API response envelope helpers (see docs/REST_API.md)."""
from __future__ import annotations

from typing import Any


def ok(data: Any = None) -> dict[str, Any]:
    return {"success": True, "data": data}


def fail(code: str, message: str, **extra: Any) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if extra:
        error.update(extra)
    return {"success": False, "error": error}
