from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_plugin_manager, require_role
from app.core.exceptions import NotFoundError
from app.db.models.user import User, UserRole
from app.plugins.manager import LoadedPlugin, PluginManager
from app.schemas.common import ok
from app.schemas.plugin import PluginSummary

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

require_admin = require_role(UserRole.ADMINISTRATOR)


def _summarize(loaded: LoadedPlugin) -> PluginSummary:
    return PluginSummary(
        id=loaded.manifest.id,
        name=loaded.manifest.name,
        version=loaded.manifest.version,
        plugin_type=loaded.manifest.plugin_type.value,
        enabled=loaded.enabled,
        status=loaded.instance.status() if loaded.enabled else {"state": "disabled"},
    )


@router.get("")
async def list_plugins(
    manager: PluginManager = Depends(get_plugin_manager),
    _: User = Depends(get_current_user),
) -> dict:
    return ok([_summarize(p).model_dump() for p in manager.plugins.values()])


@router.get("/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    _: User = Depends(get_current_user),
) -> dict:
    loaded = manager.get(plugin_id)
    if loaded is None:
        raise NotFoundError(f"Plugin '{plugin_id}' not found.", code="PLUGIN_NOT_FOUND")
    return ok(_summarize(loaded).model_dump())


@router.post("/{plugin_id}/reload")
async def reload_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    _: User = Depends(require_admin),
) -> dict:
    try:
        loaded = manager.reload(plugin_id)
    except KeyError:
        raise NotFoundError(f"Plugin '{plugin_id}' not found.", code="PLUGIN_NOT_FOUND") from None
    return ok(_summarize(loaded).model_dump())


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    _: User = Depends(require_admin),
) -> dict:
    try:
        loaded = manager.enable(plugin_id)
    except KeyError:
        raise NotFoundError(f"Plugin '{plugin_id}' not found.", code="PLUGIN_NOT_FOUND") from None
    return ok(_summarize(loaded).model_dump())


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    _: User = Depends(require_admin),
) -> dict:
    try:
        loaded = manager.disable(plugin_id)
    except KeyError:
        raise NotFoundError(f"Plugin '{plugin_id}' not found.", code="PLUGIN_NOT_FOUND") from None
    return ok(_summarize(loaded).model_dump())
