"""Scheduled recording: a job scheduled for a near-future wall-clock
time actually starts and auto-stops a real recording against the mock
plugin's capture, and cancellation actually stops it if already
running.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

pytestmark = pytest.mark.asyncio


async def test_schedule_starts_and_auto_stops(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)
    await client.post("/api/receivers/mock:0/tune", json={"frequency": 100_300_000})

    start_at = (datetime.now(UTC) + timedelta(milliseconds=200)).isoformat()
    resp = await client.post(
        "/api/receivers/mock:0/scheduled-recording",
        json={"mode": "fm", "start_at": start_at, "duration_seconds": 0.5},
    )
    assert resp.status_code == 200
    job = resp.json()["data"]
    assert job["status"] == "pending"

    recording_service = app.state.recording_service
    for _ in range(30):
        if recording_service.is_recording("mock:0"):
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("scheduled recording never started within the wait window")

    for _ in range(30):
        if not recording_service.is_recording("mock:0"):
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("scheduled recording never auto-stopped within the wait window")

    recordings = recording_service.list_recordings()
    assert any(r.filename.startswith("mock_0_fm_") for r in recordings)

    listed = await client.get("/api/receivers/mock:0/scheduled-recordings")
    assert listed.json()["data"][0]["status"] == "done"


async def test_cancel_before_start_prevents_recording(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    start_at = (datetime.now(UTC) + timedelta(seconds=2)).isoformat()
    resp = await client.post(
        "/api/receivers/mock:0/scheduled-recording",
        json={"mode": "fm", "start_at": start_at, "duration_seconds": 5},
    )
    job_id = resp.json()["data"]["id"]

    cancel_resp = await client.delete(f"/api/scheduled-recordings/{job_id}")
    assert cancel_resp.status_code == 200

    await asyncio.sleep(2.2)
    recording_service = app.state.recording_service
    assert recording_service.is_recording("mock:0") is False


async def test_cancel_while_recording_stops_it(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    start_at = datetime.now(UTC).isoformat()
    resp = await client.post(
        "/api/receivers/mock:0/scheduled-recording",
        json={"mode": "fm", "start_at": start_at, "duration_seconds": 30},
    )
    job_id = resp.json()["data"]["id"]

    recording_service = app.state.recording_service
    for _ in range(30):
        if recording_service.is_recording("mock:0"):
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("scheduled recording never started within the wait window")

    await client.delete(f"/api/scheduled-recordings/{job_id}")
    for _ in range(30):
        if not recording_service.is_recording("mock:0"):
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("cancelling a running scheduled recording never stopped it")


async def test_scheduled_recording_requires_auth(client):
    resp = await client.post(
        "/api/receivers/mock:0/scheduled-recording",
        json={"mode": "fm", "start_at": datetime.now(UTC).isoformat(), "duration_seconds": 5},
    )
    assert resp.status_code == 401
