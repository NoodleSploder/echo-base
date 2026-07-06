"""Detects receivers appearing/disappearing between discovery polls
(Phase 2: USB hot-plug monitoring) and emits `ReceiverConnected`/
`ReceiverDisconnected` events on the shared EventBus.

Reuses `ReceiverService.discover()` -- the same call `GET
/api/receivers` already makes -- rather than talking to hardware
directly, so this works for any receiver plugin, not just `rtl_sdr`.
The first discovery (`start()`) seeds the known-receiver set without
emitting anything: every receiver present at startup was already
there, not just plugged in, so treating them all as "just connected"
would be noise, not signal.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.events import Event, EventBus
from app.services.receiver_service import ReceiverService

logger = logging.getLogger("echo_base.hotplug")

DEFAULT_POLL_INTERVAL_SECONDS = 10.0


class HotplugMonitor:
    def __init__(self, receiver_service: ReceiverService, event_bus: EventBus) -> None:
        self._receiver_service = receiver_service
        self._event_bus = event_bus
        self._known_ids: set[str] = set()
        self._task: asyncio.Task | None = None

    async def start(self, interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS) -> None:
        try:
            descriptors = await self._receiver_service.discover()
            self._known_ids = {d.id for d in descriptors}
        except Exception:
            logger.exception("Initial hotplug discovery failed")
        self._task = asyncio.create_task(self._loop(interval_seconds))

    async def check_once(self) -> None:
        try:
            descriptors = await self._receiver_service.discover()
        except Exception:
            logger.exception("Hotplug discovery poll failed")
            return

        current_ids = {d.id for d in descriptors}
        for receiver_id in current_ids - self._known_ids:
            logger.info("Receiver connected: %s", receiver_id)
            await self._event_bus.publish(
                Event(type="ReceiverConnected", source=receiver_id, data={"receiver_id": receiver_id})
            )
        for receiver_id in self._known_ids - current_ids:
            logger.info("Receiver disconnected: %s", receiver_id)
            await self._event_bus.publish(
                Event(type="ReceiverDisconnected", source=receiver_id, data={"receiver_id": receiver_id})
            )
        self._known_ids = current_ids

    async def _loop(self, interval_seconds: float) -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            await self.check_once()

    def shutdown(self) -> None:
        if self._task is not None:
            self._task.cancel()
