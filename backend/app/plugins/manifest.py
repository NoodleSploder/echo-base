"""Plugin manifest schema (manifest.yaml)."""
from __future__ import annotations

import enum

from pydantic import BaseModel


class PluginType(str, enum.Enum):
    RECEIVER = "receiver"
    RADIO = "radio"
    DECODER = "decoder"
    MESSAGING = "messaging"
    DASHBOARD = "dashboard"
    RECORDING = "recording"
    AUTOMATION = "automation"
    AI = "ai"


class PluginManifest(BaseModel):
    name: str
    id: str
    version: str
    author: str = "Unknown"
    description: str = ""
    plugin_type: PluginType
    api_version: int = 1
    entry_point: str = "plugin.py"
    min_echo_base_version: str | None = None
    max_tested_version: str | None = None
