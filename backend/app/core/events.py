"""Internal asyncio event bus.

Subsystems and plugins publish domain events (``ReceiverStarted``,
``SignalDetected``, ...) instead of calling each other directly, per the
loose-coupling philosophy in ARCHITECTURE.md. The WebSocket layer
subscribes to everything and fans events out to connected clients.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("echo_base.events")

EventHandler = Callable[["Event"], Awaitable[None] | None]


@dataclass(frozen=True)
class Event:
    type: str
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


class EventBus:
    """Minimal pub/sub bus with an in-memory backlog for late subscribers."""

    def __init__(self, history_size: int = 500) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []
        self._history: deque[Event] = deque(maxlen=history_size)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the running event loop so `emit()` is safe to call from worker threads."""
        self._loop = loop

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type == "*":
            self._wildcard_subscribers.append(handler)
        else:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type == "*":
            if handler in self._wildcard_subscribers:
                self._wildcard_subscribers.remove(handler)
        elif handler in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        handlers = list(self._subscribers.get(event.type, [])) + list(self._wildcard_subscribers)
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Event handler failed for event type '%s'", event.type)

    def emit(self, event_type: str, source: str, data: dict[str, Any] | None = None) -> None:
        """Thread-safe fire-and-forget publish, for use by plugins running off the event loop."""
        event = Event(type=event_type, source=source, data=data or {})
        if self._loop is None:
            logger.warning(
                "EventBus.emit('%s') called before the event loop was bound; dropping.", event_type
            )
            return
        asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)

    def recent(self, limit: int = 100) -> list[Event]:
        return list(self._history)[-limit:]
