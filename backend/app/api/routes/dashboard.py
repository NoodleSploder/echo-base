"""Per-user dashboard layout persistence (react-grid-layout state)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ValidationAppError
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.common import ok
from app.schemas.dashboard import DashboardLayoutPayload

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/layout")
async def get_layout(user: User = Depends(get_current_user)) -> dict:
    layout = json.loads(user.dashboard_layout) if user.dashboard_layout else None
    return ok({"layout": layout})


@router.put("/layout")
async def save_layout(
    payload: DashboardLayoutPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        serialized = json.dumps(payload.layout)
    except (TypeError, ValueError) as exc:
        raise ValidationAppError(f"Layout is not JSON-serializable: {exc}") from exc

    user.dashboard_layout = serialized
    db.add(user)
    await db.commit()
    return ok({"message": "Layout saved."})
