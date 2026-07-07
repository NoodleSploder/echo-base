"""Ft8Message events get persisted (via the EventBus subscriber wired
in main.py) as "last known contact per callsign" and are queryable
back out. Same shape as test_ais_vessels.py/test_adsb_aircraft.py.
"""
from __future__ import annotations

import pytest

from app.core.events import Event
from app.services.ft8_stations import list_stations, persist_ft8_station

pytestmark = pytest.mark.asyncio


def _message_event(source: str = "mock:0", call_de: str = "K1ABC", **data_overrides):
    data = {
        "call_to": "CQ",
        "call_de": call_de,
        "extra": "FN42",
        "frequency_offset_hz": 906.2,
        "grid": "FN42",
        "latitude": 42.5,
        "longitude": -71.0,
        **data_overrides,
    }
    return Event(type="Ft8Message", source=source, data=data)


async def test_persist_and_query_round_trip(client):
    await persist_ft8_station(_message_event())

    stations = await list_stations()
    assert len(stations) == 1
    assert stations[0].callsign == "K1ABC"
    assert stations[0].receiver_id == "mock:0"
    assert stations[0].grid == "FN42"
    assert stations[0].latitude == pytest.approx(42.5)
    assert stations[0].message_count == 1


async def test_repeated_sightings_increment_count_not_duplicate(client):
    await persist_ft8_station(_message_event())
    await persist_ft8_station(_message_event(extra="-12", grid=None, latitude=None, longitude=None))
    await persist_ft8_station(_message_event(extra="RR73", grid=None, latitude=None, longitude=None))

    stations = await list_stations()
    assert len(stations) == 1
    assert stations[0].message_count == 3
    assert stations[0].last_message == "CQ K1ABC RR73"


async def test_position_not_cleared_by_a_message_without_a_grid(client):
    await persist_ft8_station(_message_event())
    await persist_ft8_station(_message_event(extra="-05", grid=None, latitude=None, longitude=None))

    stations = await list_stations()
    assert stations[0].grid == "FN42"
    assert stations[0].latitude == pytest.approx(42.5)


async def test_hashed_callsign_is_not_persisted(client):
    await persist_ft8_station(_message_event(call_de="<...>"))
    assert await list_stations() == []


async def test_query_filters_by_receiver(client):
    await persist_ft8_station(_message_event(source="mock:0", call_de="AAA1BB"))
    await persist_ft8_station(_message_event(source="mock:1", call_de="CCC2DD"))

    stations = await list_stations(receiver_id="mock:0")
    assert len(stations) == 1
    assert stations[0].callsign == "AAA1BB"


async def test_ft8_stations_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    await persist_ft8_station(_message_event())

    resp = await client.get("/api/ft8/stations")
    body = resp.json()["data"]
    assert len(body) == 1
    assert body[0]["callsign"] == "K1ABC"
    assert body[0]["grid"] == "FN42"
    assert body[0]["latitude"] == pytest.approx(42.5)


async def test_ft8_stations_requires_auth(client):
    resp = await client.get("/api/ft8/stations")
    assert resp.status_code == 401
