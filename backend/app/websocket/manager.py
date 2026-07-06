"""Tracks active WebSocket connections and fans out event bus traffic."""
from __future__ import annotations

import logging

from starlette.websockets import WebSocket, WebSocketState

from app.core.events import Event, EventBus

logger = logging.getLogger("echo_base.websocket")


class ConnectionManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._connections: set[WebSocket] = set()
        event_bus.subscribe("*", self._on_event)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WebSocket client connected (%d active)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("WebSocket client disconnected (%d active)", len(self._connections))

    async def _on_event(self, event: Event) -> None:
        if not self._connections:
            return
        payload = event.to_dict()
        stale: list[WebSocket] = []
        for connection in list(self._connections):
            if connection.client_state != WebSocketState.CONNECTED:
                stale.append(connection)
                continue
            try:
                await connection.send_json(payload)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)
