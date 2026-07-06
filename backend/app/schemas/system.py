from __future__ import annotations

from pydantic import BaseModel


class SystemInfo(BaseModel):
    name: str = "Echo Base"
    version: str
    environment: str
    hostname: str
    platform: str
    uptime_seconds: float


class HealthStatus(BaseModel):
    status: str
    database: str
    plugins_loaded: int
