from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PluginSummary(BaseModel):
    id: str
    name: str
    version: str
    plugin_type: str
    enabled: bool
    status: dict[str, Any]
