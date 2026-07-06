"""Event history (REST) and live event stream (WebSocket)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import authenticate, get_current_user, get_event_bus
from app.core.events import EventBus
from app.core.exceptions import AuthenticationError
from app.db.models.user import User
from app.db.session import get_session_factory
from app.schemas.common import ok

router = APIRouter(tags=["events"])


@router.get("/api/events")
async def recent_events(
    limit: int = 100,
    event_bus: EventBus = Depends(get_event_bus),
    _: User = Depends(get_current_user),
) -> dict:
    return ok([event.to_dict() for event in event_bus.recent(limit)])


@router.websocket("/ws/events")
async def events_stream(websocket: WebSocket) -> None:
    settings = websocket.app.state.settings
    connection_manager = websocket.app.state.connection_manager
    session_factory = get_session_factory()

    async with session_factory() as db:
        try:
            await authenticate(websocket.cookies, websocket.headers, settings, db)
        except AuthenticationError:
            await websocket.close(code=4401)
            return

    await connection_manager.connect(websocket)
    try:
        while True:
            # Server-push only for now; this just detects client disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(websocket)
