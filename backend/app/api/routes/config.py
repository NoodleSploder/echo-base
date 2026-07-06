from __future__ import annotations

from typing import Any

import yaml
from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError as PydanticValidationError

from app.api.deps import get_settings, require_role
from app.core.config import DEFAULT_CONFIG_FILE, Settings
from app.core.config import get_settings as load_settings
from app.core.exceptions import ValidationAppError
from app.core.logging import configure_logging
from app.db.models.user import User, UserRole
from app.schemas.common import ok

router = APIRouter(prefix="/api/config", tags=["config"])

require_admin = require_role(UserRole.ADMINISTRATOR)

_REDACTED_FIELDS = {"secret_key"}


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key in _REDACTED_FIELDS:
            redacted[key] = "********"
        elif isinstance(value, dict):
            redacted[key] = _redact(value)
        else:
            redacted[key] = value
    return redacted


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@router.get("")
async def get_config(settings: Settings = Depends(get_settings), _: User = Depends(require_admin)) -> dict:
    return ok(_redact(settings.model_dump(mode="json")))


@router.put("")
async def update_config(overrides: dict[str, Any], _: User = Depends(require_admin)) -> dict:
    existing: dict[str, Any] = {}
    if DEFAULT_CONFIG_FILE.exists():
        existing = yaml.safe_load(DEFAULT_CONFIG_FILE.read_text(encoding="utf-8")) or {}

    merged = _deep_merge(existing, overrides)

    try:
        Settings(**merged)
    except PydanticValidationError as exc:
        raise ValidationAppError(f"Invalid configuration: {exc}") from exc

    DEFAULT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONFIG_FILE.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")
    return ok({"message": "Configuration written. Call /api/config/reload or restart to apply."})


@router.post("/reload")
async def reload_config(request: Request, _: User = Depends(require_admin)) -> dict:
    load_settings.cache_clear()
    new_settings = load_settings()
    request.app.state.settings = new_settings
    configure_logging(new_settings)
    return ok(_redact(new_settings.model_dump(mode="json")))
