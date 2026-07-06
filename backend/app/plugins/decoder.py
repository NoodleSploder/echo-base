"""Decoder plugin contract (see docs/PLUGIN_API.md).

Wiring a Decoder Manager is Phase 5 work (see ROADMAP.md); this module
defines the stable interface so decoder plugins can already be authored
against it.
"""
from __future__ import annotations

from app.plugins.base import Plugin


class DecoderPlugin(Plugin):
    """Base class for plugins that wrap an external digital-mode decoder."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def configure(self, config: dict) -> None: ...

    def statistics(self) -> dict: ...
