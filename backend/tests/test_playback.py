"""Recorded .iq files can be played back through the same
spectrum/audio/decoder pipeline live receivers use (see
StreamService.register_playback).
"""
from __future__ import annotations

import asyncio

import pytest

from app.main import app
from app.services.stream_service import OUTPUT_BINS

pytestmark = pytest.mark.asyncio


async def _record_a_short_iq_file(client) -> str:
    start = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "iq"})
    assert start.status_code == 200
    await asyncio.sleep(0.3)
    stop = await client.post("/api/receivers/mock:0/recording/stop")
    assert stop.status_code == 200
    return stop.json()["data"]["filename"]


async def test_playback_start_stop_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    filename = await _record_a_short_iq_file(client)

    start = await client.post(f"/api/recordings/{filename}/playback/start")
    assert start.status_code == 200
    playback_id = start.json()["data"]["playback_id"]
    assert playback_id == f"playback:{filename}"

    stop = await client.post(f"/api/recordings/{filename}/playback/stop")
    assert stop.status_code == 200

    await client.delete(f"/api/recordings/{filename}")


async def test_playback_feeds_real_spectrum_pipeline(client, admin_user):
    """The whole point: subscribing to a playback_id yields real FFT
    frames computed from the recorded file's actual samples, through the
    exact same _ReceiverCapture code path a live receiver uses."""
    await client.post("/api/auth/login", json=admin_user)
    filename = await _record_a_short_iq_file(client)

    playback_start = await client.post(f"/api/recordings/{filename}/playback/start")
    playback_id = playback_start.json()["data"]["playback_id"]

    stream_service = app.state.stream_service
    queue = await stream_service.subscribe_spectrum(playback_id)
    try:
        frame = await asyncio.wait_for(queue.get(), timeout=5)
        assert len(frame) == OUTPUT_BINS * 4
    finally:
        await stream_service.unsubscribe_spectrum(playback_id, queue)
        await stream_service.unregister_playback(playback_id)
        await client.delete(f"/api/recordings/{filename}")


async def test_playback_rejects_wav_recordings(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    await client.post("/api/receivers/mock:0/recording/start", json={"mode": "fm"})
    await asyncio.sleep(0.2)
    stop = await client.post("/api/receivers/mock:0/recording/stop")
    filename = stop.json()["data"]["filename"]

    resp = await client.post(f"/api/recordings/{filename}/playback/start")
    assert resp.status_code == 422

    await client.delete(f"/api/recordings/{filename}")


async def test_playback_unknown_recording_404s(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post("/api/recordings/does-not-exist.iq/playback/start")
    assert resp.status_code == 404
