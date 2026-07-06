"""AdsbMessage events get persisted (via the EventBus subscriber wired
in main.py) as "last known contact per ICAO address" and are queryable
back out.
"""
from __future__ import annotations

import pytest

from app.core.events import Event
from app.services.adsb_aircraft import list_aircraft, persist_adsb_aircraft

pytestmark = pytest.mark.asyncio


def _message_event(source: str = "mock:0", icao: str = "4840D6", **data_overrides):
    data = {"hex": "8D4840D6...", "df": 17, "icao": icao, "type_code": 4, **data_overrides}
    return Event(type="AdsbMessage", source=source, data=data)


async def test_persist_and_query_round_trip(client):
    await persist_adsb_aircraft(_message_event())

    aircraft = await list_aircraft()
    assert len(aircraft) == 1
    assert aircraft[0].icao == "4840D6"
    assert aircraft[0].receiver_id == "mock:0"
    assert aircraft[0].message_count == 1


async def test_repeated_sightings_increment_count_not_duplicate(client):
    await persist_adsb_aircraft(_message_event())
    await persist_adsb_aircraft(_message_event(type_code=1))
    await persist_adsb_aircraft(_message_event(type_code=11))

    aircraft = await list_aircraft()
    assert len(aircraft) == 1
    assert aircraft[0].message_count == 3
    assert aircraft[0].last_type_code == 11


async def test_query_filters_by_receiver(client):
    await persist_adsb_aircraft(_message_event(source="mock:0", icao="AAAAAA"))
    await persist_adsb_aircraft(_message_event(source="mock:1", icao="BBBBBB"))

    aircraft = await list_aircraft(receiver_id="mock:0")
    assert len(aircraft) == 1
    assert aircraft[0].icao == "AAAAAA"


async def test_adsb_aircraft_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    await persist_adsb_aircraft(_message_event())

    resp = await client.get("/api/adsb/aircraft")
    body = resp.json()["data"]
    assert len(body) == 1
    assert body[0]["icao"] == "4840D6"
    assert body[0]["message_count"] == 1


async def test_adsb_aircraft_requires_auth(client):
    resp = await client.get("/api/adsb/aircraft")
    assert resp.status_code == 401
