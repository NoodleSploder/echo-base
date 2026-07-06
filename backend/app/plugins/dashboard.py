"""Dashboard plugin contract (see docs/PLUGIN_API.md).

Dashboard plugin loading (widgets/routes/menu items) is future work;
this module defines the stable interface so contributors can already
author against it.
"""
from __future__ import annotations

from app.plugins.base import Plugin


class DashboardPlugin(Plugin):
    """Base class for plugins that contribute frontend UI contributions."""

    def routes(self) -> list: ...

    def widgets(self) -> list: ...

    def menu_items(self) -> list: ...
