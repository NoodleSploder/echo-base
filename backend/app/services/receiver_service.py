"""Receiver Manager: aggregates receiver plugins behind a single API.

Hardware I/O is blocking, so every plugin call is dispatched through
``asyncio.to_thread`` to keep the event loop free (see
docs/PLUGIN_API.md's "Avoid blocking the event loop" guidance).
"""
from __future__ import annotations

import asyncio
import logging

from app.core.exceptions import NotFoundError
from app.plugins.manager import PluginManager
from app.plugins.receiver import ReceiverDescriptor, ReceiverPlugin, ReceiverStatus

logger = logging.getLogger("echo_base.receivers")


class ReceiverNotFoundError(NotFoundError):
    code = "RECEIVER_NOT_FOUND"


class ReceiverService:
    def __init__(self, plugin_manager: PluginManager) -> None:
        self._plugin_manager = plugin_manager
        self._registry: dict[str, str] = {}  # receiver_id -> plugin_id

    def _receiver_plugins(self) -> list[tuple[str, ReceiverPlugin]]:
        return [
            (loaded.manifest.id, loaded.instance)
            for loaded in self._plugin_manager.by_type("receiver")
            if isinstance(loaded.instance, ReceiverPlugin)
        ]

    async def discover(self) -> list[ReceiverDescriptor]:
        descriptors: list[ReceiverDescriptor] = []
        for plugin_id, plugin in self._receiver_plugins():
            try:
                found = await asyncio.to_thread(plugin.discover)
            except Exception:
                logger.exception("Receiver plugin '%s' failed to discover devices", plugin_id)
                continue
            for descriptor in found:
                self._registry[descriptor.id] = plugin_id
                descriptors.append(descriptor)
        return descriptors

    async def list_receivers(self) -> list[ReceiverDescriptor]:
        # Re-run discovery so the list always reflects currently attached hardware.
        return await self.discover()

    async def _resolve(self, receiver_id: str) -> ReceiverPlugin:
        plugin_id = self._registry.get(receiver_id)
        if plugin_id is None:
            await self.discover()
            plugin_id = self._registry.get(receiver_id)
        if plugin_id is None:
            raise ReceiverNotFoundError(f"Receiver '{receiver_id}' does not exist.")

        loaded = self._plugin_manager.get(plugin_id)
        if loaded is None or not loaded.enabled or not isinstance(loaded.instance, ReceiverPlugin):
            raise ReceiverNotFoundError(f"Receiver '{receiver_id}' does not exist.")
        return loaded.instance

    async def start(self, receiver_id: str) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        status = await asyncio.to_thread(plugin.start, receiver_id)
        plugin.context.emit("ReceiverStarted", {"receiver_id": receiver_id})
        return status

    async def stop(self, receiver_id: str) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        status = await asyncio.to_thread(plugin.stop, receiver_id)
        plugin.context.emit("ReceiverStopped", {"receiver_id": receiver_id})
        return status

    async def tune(self, receiver_id: str, frequency_hz: int) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.tune, receiver_id, frequency_hz)

    async def set_gain(self, receiver_id: str, gain: str | float) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.set_gain, receiver_id, gain)

    async def set_bandwidth(self, receiver_id: str, bandwidth_hz: int) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.set_bandwidth, receiver_id, bandwidth_hz)

    async def set_sample_rate(self, receiver_id: str, sample_rate_hz: int) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.set_sample_rate, receiver_id, sample_rate_hz)

    async def set_ppm_correction(self, receiver_id: str, ppm: int) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.set_ppm_correction, receiver_id, ppm)

    async def status(self, receiver_id: str) -> ReceiverStatus:
        plugin = await self._resolve(receiver_id)
        return await asyncio.to_thread(plugin.device_status, receiver_id)

    async def resolve_plugin(self, receiver_id: str) -> ReceiverPlugin:
        """Exposes plugin lookup for callers that need to drive the plugin
        directly, e.g. StreamService opening a raw IQ stream."""
        return await self._resolve(receiver_id)
