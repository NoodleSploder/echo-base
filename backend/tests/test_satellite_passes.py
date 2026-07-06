"""Satellite pass prediction: pure topocentric geometry sanity checks,
plus an end-to-end SGP4 propagation test against a real TLE (fetched
from Celestrak on 2026-07-06 for NOAA 15 -- will go stale, which is
exactly the point being tested elsewhere: this module never ships or
caches TLE data of its own).
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.satellite_passes import (
    EARTH_RADIUS_KM,
    _observer_ecef,
    _topocentric_elevation_deg,
    find_passes,
)

# Real TLE, fetched directly from Celestrak (NOAA 15, catalog #25338) --
# used here only to sanity-check the propagation pipeline runs and
# returns plausible values, not as a permanently-valid orbital state.
NOAA_15_TLE = (
    "1 25338U 98030A   26187.25559808  .00000133  00000+0  71966-4 0  9996",
    "2 25338  98.5062 207.3726 0009082 294.5375  65.4859 14.27152357464013",
)


def test_point_directly_overhead_reads_ninety_degrees():
    lat, lon = 40.0, -105.0
    obs_x, obs_y, obs_z = _observer_ecef(lat, lon, 0.0)
    # A point 500km further out along the same observer-to-center
    # radial line is, by construction, directly overhead.
    scale = (EARTH_RADIUS_KM + 500) / EARTH_RADIUS_KM
    overhead = (obs_x * scale, obs_y * scale, obs_z * scale)

    elevation = _topocentric_elevation_deg(overhead, lat, lon, 0.0)
    assert elevation == pytest.approx(90.0, rel=1e-6)


def test_point_on_opposite_side_of_earth_is_well_below_horizon():
    lat, lon = 40.0, -105.0
    # The antipodal point, pushed out radially -- unambiguously below
    # the horizon from the original observer's position.
    anti_lat, anti_lon = -lat, lon + 180.0
    anti_x, anti_y, anti_z = _observer_ecef(anti_lat, anti_lon, 500_000.0)

    elevation = _topocentric_elevation_deg((anti_x, anti_y, anti_z), lat, lon, 0.0)
    assert elevation < -45.0


def test_find_passes_against_real_tle_runs_and_returns_plausible_data():
    """Not a "does it predict the exact real pass" test (no independent
    ground-truth source for that here) -- confirms the full SGP4 ->
    ECEF -> topocentric pipeline runs against a real orbital state
    without error and produces internally-consistent results (LOS
    after AOS, a plausible max elevation) for however many passes a
    real polar orbiter makes over 24h, which for NOAA 15 over any
    given mid-latitude ground station is reliably several."""
    tle1, tle2 = NOAA_15_TLE
    passes = find_passes(
        tle1,
        tle2,
        latitude_deg=40.0,
        longitude_deg=-105.0,
        elevation_m=1600.0,
        start_at=datetime.now(UTC),
        hours=24,
        min_elevation_deg=10.0,
    )

    assert len(passes) >= 1
    for satellite_pass in passes:
        assert satellite_pass.los_at > satellite_pass.aos_at
        assert 10.0 <= satellite_pass.max_elevation_deg <= 90.0
        assert satellite_pass.los_at - satellite_pass.aos_at < timedelta(minutes=20)


@pytest.mark.asyncio
async def test_predict_passes_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    tle1, tle2 = NOAA_15_TLE

    resp = await client.post(
        "/api/satellites/passes",
        json={
            "tle_line1": tle1,
            "tle_line2": tle2,
            "latitude_deg": 40.0,
            "longitude_deg": -105.0,
            "elevation_m": 1600.0,
            "hours": 24,
            "min_elevation_deg": 10.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert len(body) >= 1
    assert body[0]["los_at"] > body[0]["aos_at"]


@pytest.mark.asyncio
async def test_predict_passes_rejects_garbage_tle(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post(
        "/api/satellites/passes",
        json={
            "tle_line1": "not a tle",
            "tle_line2": "not a tle either",
            "latitude_deg": 40.0,
            "longitude_deg": -105.0,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_predict_passes_requires_auth(client):
    resp = await client.post(
        "/api/satellites/passes",
        json={"tle_line1": "x", "tle_line2": "y", "latitude_deg": 0, "longitude_deg": 0},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_schedule_next_pass_recording(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)
    tle1, tle2 = NOAA_15_TLE

    resp = await client.post(
        "/api/satellites/mock:0/schedule-next-pass",
        json={
            "tle_line1": tle1,
            "tle_line2": tle2,
            "latitude_deg": 40.0,
            "longitude_deg": -105.0,
            "elevation_m": 1600.0,
            "hours": 24,
            "min_elevation_deg": 10.0,
            "mode": "fm",
            "frequency_hz": 137620000,
        },
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["los_at"] > body["aos_at"]
    assert body["duration_seconds"] > 0

    scheduled_recording_service = app.state.scheduled_recording_service
    jobs = scheduled_recording_service.list_jobs("mock:0")
    assert any(job.id == body["job_id"] for job in jobs)

    status = await client.get("/api/receivers/mock:0")
    assert status.json()["data"]["frequency_hz"] == 137620000

    scheduled_recording_service.cancel(body["job_id"])


@pytest.mark.asyncio
async def test_schedule_next_pass_404s_when_no_pass_in_window(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    tle1, tle2 = NOAA_15_TLE

    resp = await client.post(
        "/api/satellites/mock:0/schedule-next-pass",
        json={
            "tle_line1": tle1,
            "tle_line2": tle2,
            "latitude_deg": 40.0,
            "longitude_deg": -105.0,
            "hours": 0.01,
            "min_elevation_deg": 89.9,
        },
    )
    assert resp.status_code == 404
