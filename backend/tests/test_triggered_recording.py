"""Triggered recording: arming a receiver makes a real SignalDetected
event start a real recording, which then auto-stops after
duration_seconds -- exercised end-to-end against the mock plugin's
capture, not just a stubbed unit test of the handler.
"""
from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def test_arm_and_real_detection_starts_and_stops_recording(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)
    await client.post("/api/receivers/mock:0/tune", json={"frequency": 100_300_000})

    resp = await client.post(
        "/api/receivers/mock:0/triggered-recording/start", json={"mode": "fm", "duration_seconds": 0.5}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["armed"] is True

    stream_service = app.state.stream_service
    # A tiny margin so the mock plugin's random IQ noise reliably
    # produces at least one detection within the wait below.
    await stream_service.enable_signal_detection("mock:0", margin_db=0.1, center_frequency_hz=None)
    try:
        recording_service = app.state.recording_service
        for _ in range(30):
            if recording_service.is_recording("mock:0"):
                break
            await asyncio.sleep(0.2)
        else:
            pytest.fail("triggered recording never started within the wait window")

        # Disarm signal detection immediately so the mock plugin's
        # continuous noise can't re-trigger a second recording the
        # instant this one auto-stops -- that race (not a real bug,
        # just this test's own timing) would otherwise make the
        # eventual list_recordings() check flaky.
        await stream_service.disable_signal_detection("mock:0")

        # Auto-stop fires after duration_seconds -- confirm it actually
        # stops on its own rather than needing a manual stop call.
        for _ in range(30):
            if not recording_service.is_recording("mock:0"):
                break
            await asyncio.sleep(0.2)
        else:
            pytest.fail("triggered recording never auto-stopped within the wait window")

        # receiver_id on a since-stopped RecordingInfo is reconstructed
        # from the (sanitized, ":" -> "_") filename rather than the
        # tracked value -- see recording_service.py's _describe_file --
        # so this checks the filename prefix, not receiver_id, for the
        # same reason test_recording_service-style tests do.
        recordings = recording_service.list_recordings()
        assert any(r.filename.startswith("mock_0_fm_") for r in recordings)
    finally:
        await stream_service.disable_signal_detection("mock:0")
        await client.post("/api/receivers/mock:0/triggered-recording/stop")


async def test_disarm_stops_new_triggers(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    await client.post(
        "/api/receivers/mock:0/triggered-recording/start", json={"mode": "fm", "duration_seconds": 5}
    )
    resp = await client.post("/api/receivers/mock:0/triggered-recording/stop")
    assert resp.json()["data"]["armed"] is False

    triggered_recording_service = app.state.triggered_recording_service
    assert triggered_recording_service.is_armed("mock:0") is False


async def test_capture_health_reports_armed_state(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/receivers/mock:0/capture-health")
    assert resp.json()["data"]["triggered_recording_armed"] is False

    await client.post(
        "/api/receivers/mock:0/triggered-recording/start", json={"mode": "fm", "duration_seconds": 5}
    )
    resp = await client.get("/api/receivers/mock:0/capture-health")
    assert resp.json()["data"]["triggered_recording_armed"] is True

    await client.post("/api/receivers/mock:0/triggered-recording/stop")


async def test_triggered_recording_requires_auth(client):
    resp = await client.post(
        "/api/receivers/mock:0/triggered-recording/start", json={"mode": "fm", "duration_seconds": 5}
    )
    assert resp.status_code == 401
