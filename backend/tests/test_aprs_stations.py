"""Position-bearing AprsPacket events get persisted (via the EventBus
subscriber wired in main.py) as "last known position per station" and
are queryable back out.
"""
from __future__ import annotations

import pytest

from app.core.events import Event
from app.services.aprs_stations import persist_aprs_station, query_aprs_stations

pytestmark = pytest.mark.asyncio


def _packet_event(source: str = "mock:0", callsign: str = "N0CALL", **data_overrides):
    data = {
        "source": callsign,
        "destination": "APRS",
        "path": "WIDE1-1",
        "info": "!4903.50N/07201.75W-Test",
        "latitude": 49.0583,
        "longitude": -72.0292,
        "symbol": "/-",
        **data_overrides,
    }
    return Event(type="AprsPacket", source=source, data=data)


async def test_persist_and_query_round_trip(client):
    await persist_aprs_station(_packet_event())

    stations = await query_aprs_stations()
    assert len(stations) == 1
    assert stations[0].callsign == "N0CALL"
    assert stations[0].receiver_id == "mock:0"
    assert stations[0].latitude == pytest.approx(49.0583)
    assert stations[0].longitude == pytest.approx(-72.0292)


async def test_second_report_updates_rather_than_duplicates(client):
    await persist_aprs_station(_packet_event(latitude=49.0, longitude=-72.0))
    await persist_aprs_station(_packet_event(latitude=50.0, longitude=-73.0))

    stations = await query_aprs_stations()
    assert len(stations) == 1
    assert stations[0].latitude == pytest.approx(50.0)
    assert stations[0].longitude == pytest.approx(-73.0)


async def test_packet_without_position_is_not_persisted(client):
    event = _packet_event()
    del event.data["latitude"]
    del event.data["longitude"]
    await persist_aprs_station(event)

    assert await query_aprs_stations() == []


async def test_query_filters_by_receiver(client):
    await persist_aprs_station(_packet_event(source="mock:0", callsign="AAA"))
    await persist_aprs_station(_packet_event(source="mock:1", callsign="BBB"))

    stations = await query_aprs_stations(receiver_id="mock:0")
    assert len(stations) == 1
    assert stations[0].callsign == "AAA"


async def test_aprs_stations_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    await persist_aprs_station(_packet_event())

    resp = await client.get("/api/aprs/stations")
    body = resp.json()["data"]
    assert len(body) == 1
    assert body[0]["callsign"] == "N0CALL"
    assert body[0]["latitude"] == pytest.approx(49.0583)
