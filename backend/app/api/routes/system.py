from __future__ import annotations

import os
import platform
import resource
import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.api.deps import get_current_user, get_plugin_manager, get_settings
from app.core.config import Settings
from app.db.models.user import User
from app.db.session import get_db
from app.plugins.manager import PluginManager
from app.schemas.common import ok
from app.schemas.system import HealthStatus, SystemInfo

router = APIRouter(prefix="/api/system", tags=["system"])

_START_TIME = time.monotonic()


@router.get("")
async def system_info(
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> dict:
    return ok(
        SystemInfo(
            version=__version__,
            environment=settings.environment,
            hostname=platform.node(),
            platform=f"{platform.system()} {platform.release()}",
            uptime_seconds=time.monotonic() - _START_TIME,
        ).model_dump()
    )


@router.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """Unauthenticated liveness/readiness probe for monitoring and load balancers."""
    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "unavailable"

    return ok(
        HealthStatus(
            status="ok" if database_status == "connected" else "degraded",
            database=database_status,
            plugins_loaded=len(plugin_manager.plugins),
        ).model_dump()
    )


@router.get("/metrics")
async def metrics(_: User = Depends(get_current_user)) -> dict:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cpu_times = os.times()
    return ok(
        {
            "process": {
                "max_rss_kb": usage.ru_maxrss,
                "user_cpu_seconds": cpu_times.user,
                "system_cpu_seconds": cpu_times.system,
            },
            "uptime_seconds": time.monotonic() - _START_TIME,
        }
    )
