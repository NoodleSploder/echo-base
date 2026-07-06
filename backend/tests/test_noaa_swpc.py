"""NOAA SWPC provider: parses real-shaped Kp/aurora responses correctly
(via httpx.MockTransport, same approach as test_n2yo.py -- no live
network call needed to validate parsing against NOAA's documented
response shape), renders a synthetic aurora grid to a real PNG with
correct coordinate remapping, and SpaceWeatherService keeps
last-known-good data across a failed refresh.
"""
from __future__ import annotations

import io

import httpx
import numpy as np
import pytest
from PIL import Image

from app.services.noaa_swpc import (
    AURORA_URL,
    KP_INDEX_URL,
    AuroraGrid,
    SpaceWeatherService,
    SwpcError,
    fetch_aurora_grid,
    fetch_kp_index,
    render_aurora_png,
)


def _mock_client(handler):
    real_async_client = httpx.AsyncClient

    def _patched_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    return _patched_client


async def test_fetch_kp_index_parses_real_shaped_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(KP_INDEX_URL)
        return httpx.Response(
            200,
            json=[
                {"time_tag": "2026-07-06T00:00:00", "Kp": 1.0, "a_running": 4, "station_count": 8},
                {"time_tag": "2026-07-06T03:00:00", "Kp": 2.33, "a_running": 9, "station_count": 8},
            ],
        )

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    readings = await fetch_kp_index()
    assert len(readings) == 2
    assert readings[-1]["Kp"] == 2.33


async def test_fetch_kp_index_raises_on_empty_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    with pytest.raises(SwpcError):
        await fetch_kp_index()


async def test_fetch_aurora_grid_parses_real_shaped_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(AURORA_URL)
        return httpx.Response(
            200,
            json={
                "Observation Time": "2026-07-06T21:22:00Z",
                "Forecast Time": "2026-07-06T22:25:00Z",
                "Data Format": "[Longitude, Latitude, Aurora]",
                "coordinates": [[0, -90, 4], [0, -89, 0], [10, 80, 55]],
            },
        )

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    grid = await fetch_aurora_grid()
    assert grid.observation_time == "2026-07-06T21:22:00Z"
    assert (10, 80, 55) in grid.points


async def test_fetch_aurora_grid_raises_on_missing_coordinates(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Observation Time": "x"})

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    with pytest.raises(SwpcError):
        await fetch_aurora_grid()


def test_render_aurora_png_places_points_at_correct_pixel():
    # A single hot point at lon=0 (Greenwich), lat=90 (north pole).
    # After the -180-shift, lon=0 should land at the horizontal center
    # of the image; after the vertical flip, lat=90 should land at
    # row 0 (the top).
    grid = AuroraGrid(observation_time="t1", forecast_time="t2", points=[(0, 90, 100)])
    png_bytes = render_aurora_png(grid)

    image = Image.open(io.BytesIO(png_bytes))
    assert image.size == (360, 181)
    assert image.mode == "RGBA"

    pixels = image.load()
    center_x = 180  # lon=0 shifted to the middle of a 360-wide image
    top_row = 0  # lat=90 (north) at the top
    r, g, b, a = pixels[center_x, top_row]
    assert a > 0  # the hot point is visible (non-transparent)

    # Far from the hot point, the sky should be fully transparent.
    r2, g2, b2, a2 = pixels[0, 180]  # lon=-180, lat=-90 (opposite corner)
    assert a2 == 0


def test_render_aurora_png_zero_probability_is_fully_transparent():
    grid = AuroraGrid(observation_time="t1", forecast_time="t2", points=[])  # no data at all -> all zero
    png_bytes = render_aurora_png(grid)
    image = Image.open(io.BytesIO(png_bytes))
    alpha_channel = np.array(image)[..., 3]
    assert np.all(alpha_channel == 0)


async def test_space_weather_service_keeps_last_good_data_on_failure(monkeypatch):
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            reading = {"time_tag": "2026-07-06T00:00:00", "Kp": 3.0, "a_running": 15, "station_count": 8}
            return httpx.Response(200, json=[reading])
        return httpx.Response(500)

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    service = SpaceWeatherService()
    assert service.get_kp() is None

    await service.refresh_kp()
    first = service.get_kp()
    assert first is not None
    assert first["readings"][0]["Kp"] == 3.0

    await service.refresh_kp()  # this one 500s
    second = service.get_kp()
    assert second["readings"] == first["readings"]  # unchanged, not cleared
