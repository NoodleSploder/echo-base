"""Automation plugin contract (see docs/PLUGIN_API.md).

Wiring the Automation Engine is Phase 10 work (see ROADMAP.md); this
module defines the stable interface so automation plugins can already
be authored against it.
"""
from __future__ import annotations

from app.plugins.base import Plugin


class AutomationPlugin(Plugin):
    """Base class for plugins that contribute automation triggers/actions."""

    def triggers(self) -> list: ...

    def actions(self) -> list: ...
