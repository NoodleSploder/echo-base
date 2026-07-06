from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DashboardLayoutPayload(BaseModel):
    # Keyed by react-grid-layout breakpoint (lg/md/sm/...) -> list of
    # {i, x, y, w, h, ...} items. Opaque to the backend; stored as JSON.
    layout: dict[str, Any]


class DashboardLayoutResponse(BaseModel):
    layout: dict[str, Any] | None
