"""Base plugin contract shared by every plugin category.

See docs/PLUGIN_API.md for the full design. Plugins never call each
other directly; they publish events through the shared EventBus.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.events import EventBus


@dataclass
class PluginContext:
    """Everything a plugin instance needs from the host application."""

    plugin_id: str
    config: dict[str, Any]
    logger: logging.Logger
    event_bus: EventBus

    def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        self.event_bus.emit(event_type, source=f"plugin:{self.plugin_id}", data=data)


class Plugin:
    """Base class for every Echo Base plugin."""

    def __init__(self, context: PluginContext) -> None:
        self.context = context

    @property
    def config(self) -> dict[str, Any]:
        return self.context.config

    @property
    def logger(self) -> logging.Logger:
        return self.context.logger

    def initialize(self) -> None:
        """Called once when the plugin is loaded."""

    def shutdown(self) -> None:
        """Called before the plugin is unloaded."""

    def status(self) -> dict[str, Any]:
        """Plugin-level health, not device status (see ReceiverPlugin.status)."""
        return {"state": "ready"}
