"""AisMessage events get persisted (via the EventBus subscriber wired
in main.py) as "last known contact per MMSI" and are queryable back
out.
"""
from __future__ import annotations

import pytest

from app.core.events import Event
from app.services.ais_vessels import list_vessels, persist_ais_vessel

pytestmark = pytest.mark.asyncio


def _message_event(source: str = "mock:0", mmsi: int = 123456789, **data_overrides):
    data = {"message_type": 1, "mmsi": mmsi, **data_overrides}
    return Event(type="AisMessage", source=source, data=data)


async def test_persist_and_query_round_trip(client):
    await persist_ais_vessel(_message_event())

    vessels = await list_vessels()
    assert len(vessels) == 1
    assert vessels[0].mmsi == 123456789
    assert vessels[0].receiver_id == "mock:0"
    assert vessels[0].message_count == 1


async def test_repeated_sightings_increment_count_not_duplicate(client):
    await persist_ais_vessel(_message_event())
    await persist_ais_vessel(_message_event(message_type=5))
    await persist_ais_vessel(_message_event(message_type=18))

    vessels = await list_vessels()
    assert len(vessels) == 1
    assert vessels[0].message_count == 3
    assert vessels[0].last_message_type == 18


async def test_query_filters_by_receiver(client):
    await persist_ais_vessel(_message_event(source="mock:0", mmsi=111))
    await persist_ais_vessel(_message_event(source="mock:1", mmsi=222))

    vessels = await list_vessels(receiver_id="mock:0")
    assert len(vessels) == 1
    assert vessels[0].mmsi == 111


async def test_ais_vessels_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    await persist_ais_vessel(_message_event())

    resp = await client.get("/api/ais/vessels")
    body = resp.json()["data"]
    assert len(body) == 1
    assert body[0]["mmsi"] == 123456789
    assert body[0]["message_count"] == 1


async def test_ais_vessels_requires_auth(client):
    resp = await client.get("/api/ais/vessels")
    assert resp.status_code == 401
