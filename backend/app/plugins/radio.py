"""Radio plugin contract (see docs/PLUGIN_API.md).

Radio Manager wiring is Phase 3 work (see ROADMAP.md); this module
defines the stable interface so radio plugins can already be authored
against it.
"""
from __future__ import annotations

from app.plugins.base import Plugin


class RadioPlugin(Plugin):
    """Base class for plugins that control a conventional transceiver."""

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def frequency(self) -> int | None: ...

    def set_frequency(self, hz: int) -> None: ...

    def mode(self) -> str | None: ...

    def set_mode(self, mode: str) -> None: ...

    def ptt(self, state: bool) -> None: ...

    def status(self) -> dict: ...
