"""SignalDetected events get persisted (via the EventBus subscriber
wired in main.py) and are queryable back out, distinct from the
in-memory /api/events history which is bounded and lost on restart.
"""
from __future__ import annotations

import pytest

from app.core.events import Event
from app.services.signal_history import persist_signal_detected, query_signal_history

pytestmark = pytest.mark.asyncio


async def test_persist_and_query_round_trip(client):
    event = Event(
        type="SignalDetected",
        source="mock:0",
        data={"frequency_hz": 100_300_000.0, "frequency_offset_hz": 500.0, "power_db": 12.5},
    )
    await persist_signal_detected(event)

    records = await query_signal_history("mock:0")
    assert len(records) == 1
    assert records[0].receiver_id == "mock:0"
    assert records[0].frequency_hz == pytest.approx(100_300_000.0)
    assert records[0].power_db == pytest.approx(12.5)


async def test_query_filters_by_receiver(client):
    await persist_signal_detected(
        Event(type="SignalDetected", source="mock:0", data={"frequency_offset_hz": 1.0, "power_db": 1.0})
    )
    await persist_signal_detected(
        Event(type="SignalDetected", source="mock:1", data={"frequency_offset_hz": 2.0, "power_db": 2.0})
    )

    records = await query_signal_history("mock:0")
    assert len(records) == 1
    assert records[0].receiver_id == "mock:0"


async def test_query_respects_limit(client):
    for i in range(5):
        await persist_signal_detected(
            Event(
                type="SignalDetected",
                source="mock:0",
                data={"frequency_offset_hz": float(i), "power_db": float(i)},
            )
        )

    records = await query_signal_history("mock:0", limit=3)
    assert len(records) == 3


async def test_signal_history_via_rest_reflects_real_detection(client, admin_user):
    """End-to-end: enabling signal detection on a real capture (the mock
    plugin) and letting it run should eventually produce a persisted,
    queryable record via the REST endpoint -- not just a stubbed unit
    test of the subscriber function."""
    import asyncio

    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    stream_service = app.state.stream_service
    # A tiny margin so the mock plugin's random IQ noise reliably produces
    # at least one detection within the wait below.
    await stream_service.enable_signal_detection("mock:0", margin_db=0.1, center_frequency_hz=None)
    try:
        for _ in range(20):
            resp = await client.get("/api/receivers/mock:0/signal-history")
            if resp.json()["data"]:
                break
            await asyncio.sleep(0.2)
        else:
            pytest.fail("no signal history recorded within the wait window")

        assert resp.status_code == 200
        assert len(resp.json()["data"]) > 0
    finally:
        await stream_service.disable_signal_detection("mock:0")


async def test_signal_history_requires_auth(client):
    resp = await client.get("/api/receivers/mock:0/signal-history")
    assert resp.status_code == 401
