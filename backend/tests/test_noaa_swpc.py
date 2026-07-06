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
    SOLAR_WIND_MAG_URL,
    SOLAR_WIND_SPEED_URL,
    XRAY_FLUX_URL,
    AuroraGrid,
    SpaceWeatherService,
    SwpcError,
    classify_xray_flux,
    fetch_aurora_grid,
    fetch_kp_index,
    fetch_solar_wind,
    fetch_xray_flux,
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


def test_classify_xray_flux_known_reference_values():
    # Real GOES classification reference points -- e.g. a flux of
    # 2.4e-6 W/m^2 is a C2.4 flare (C-class starts at 1e-6).
    assert classify_xray_flux(2.4e-6) == "C2.4"
    assert classify_xray_flux(1.2e-5) == "M1.2"
    assert classify_xray_flux(3.4e-4) == "X3.4"
    assert classify_xray_flux(5.0e-8) == "A5.0"


async def test_fetch_xray_flux_filters_to_long_channel(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(XRAY_FLUX_URL)
        return httpx.Response(
            200,
            json=[
                {"time_tag": "t1", "satellite": 18, "flux": 9e-8, "energy": "0.05-0.4nm"},
                {"time_tag": "t1", "satellite": 18, "flux": 2.4e-6, "energy": "0.1-0.8nm"},
                {"time_tag": "t2", "satellite": 18, "flux": 2.5e-6, "energy": "0.1-0.8nm"},
            ],
        )

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    readings = await fetch_xray_flux()
    assert len(readings) == 2
    assert all(r["energy"] == "0.1-0.8nm" for r in readings)
    assert readings[-1]["flux"] == 2.5e-6


async def test_fetch_xray_flux_raises_when_no_long_channel(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"time_tag": "t1", "flux": 9e-8, "energy": "0.05-0.4nm"}])

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    with pytest.raises(SwpcError):
        await fetch_xray_flux()


async def test_fetch_solar_wind_combines_mag_and_speed(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith(SOLAR_WIND_MAG_URL):
            return httpx.Response(200, json=[{"bt": 6, "bz_gsm": -1, "time_tag": "2026-07-06T21:54:00Z"}])
        assert url.startswith(SOLAR_WIND_SPEED_URL)
        return httpx.Response(200, json=[{"proton_speed": 427, "time_tag": "2026-07-06T21:54:00Z"}])

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))
    reading = await fetch_solar_wind()
    assert reading["bt_nt"] == 6
    assert reading["bz_gsm_nt"] == -1
    assert reading["proton_speed_km_s"] == 427


async def test_space_weather_service_xray_and_solar_wind_via_refresh(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith(XRAY_FLUX_URL):
            return httpx.Response(
                200, json=[{"time_tag": "t1", "flux": 2.4e-6, "energy": "0.1-0.8nm"}]
            )
        if url.startswith(SOLAR_WIND_MAG_URL):
            return httpx.Response(200, json=[{"bt": 6, "bz_gsm": -1, "time_tag": "t1"}])
        assert url.startswith(SOLAR_WIND_SPEED_URL)
        return httpx.Response(200, json=[{"proton_speed": 427, "time_tag": "t1"}])

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    service = SpaceWeatherService()
    assert service.get_xray() is None
    assert service.get_solar_wind() is None

    await service.refresh_xray()
    xray = service.get_xray()
    assert xray["latest_class"] == "C2.4"

    await service.refresh_solar_wind()
    solar_wind = service.get_solar_wind()
    assert solar_wind["proton_speed_km_s"] == 427
