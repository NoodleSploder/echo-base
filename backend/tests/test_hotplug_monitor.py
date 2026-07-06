"""HotplugMonitor: seeding is silent (nothing "just connected" at
startup was actually just plugged in), and later diffs against a
fresh discovery correctly emit ReceiverConnected/ReceiverDisconnected.

Tested against fakes rather than the mock plugin fixture, since the
mock plugin's discover() always returns the same fixed receiver --
this is pure diffing logic, easiest to exercise directly.
"""
from __future__ import annotations

import asyncio

import pytest

from app.core.events import Event, EventBus
from app.plugins.receiver import ReceiverDescriptor
from app.services.hotplug_monitor import HotplugMonitor

pytestmark = pytest.mark.asyncio


class _FakeReceiverService:
    def __init__(self, batches: list[list[ReceiverDescriptor]]) -> None:
        self._batches = batches
        self._index = 0

    async def discover(self) -> list[ReceiverDescriptor]:
        batch = self._batches[min(self._index, len(self._batches) - 1)]
        self._index += 1
        return batch


def _descriptor(receiver_id: str) -> ReceiverDescriptor:
    return ReceiverDescriptor(id=receiver_id, name=receiver_id, driver="fake")


async def _collect_events(bus: EventBus) -> list[Event]:
    collected: list[Event] = []

    async def handler(event: Event) -> None:
        collected.append(event)

    bus.subscribe("*", handler)
    return collected


async def test_start_seeds_without_emitting():
    bus = EventBus()
    bus.bind_loop(asyncio.get_running_loop())
    events = await _collect_events(bus)

    fake = _FakeReceiverService([[_descriptor("rtl_sdr:1")]])
    monitor = HotplugMonitor(fake, bus)
    await monitor.start(interval_seconds=3600)
    try:
        assert events == []
    finally:
        monitor.shutdown()


async def test_check_once_emits_connected_and_disconnected():
    bus = EventBus()
    bus.bind_loop(asyncio.get_running_loop())
    events = await _collect_events(bus)

    fake = _FakeReceiverService(
        [
            [_descriptor("rtl_sdr:1")],
            [_descriptor("rtl_sdr:1"), _descriptor("rtl_sdr:2")],
            [_descriptor("rtl_sdr:2")],
        ]
    )
    monitor = HotplugMonitor(fake, bus)
    await monitor.start(interval_seconds=3600)

    await monitor.check_once()
    assert [(e.type, e.source) for e in events] == [("ReceiverConnected", "rtl_sdr:2")]

    await monitor.check_once()
    assert [(e.type, e.source) for e in events] == [
        ("ReceiverConnected", "rtl_sdr:2"),
        ("ReceiverDisconnected", "rtl_sdr:1"),
    ]

    monitor.shutdown()
