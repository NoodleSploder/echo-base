import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def test_recording_lifecycle_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "fm"})
    assert start.status_code == 200
    assert start.json()["data"]["active"] is True
    assert start.json()["data"]["receiver_id"] == "mock:0"

    # Let a little real audio accumulate so the WAV file has real frames.
    await asyncio.sleep(0.3)

    listing = await client.get("/api/recordings")
    assert listing.status_code == 200
    active_entries = [r for r in listing.json()["data"] if r["active"]]
    assert len(active_entries) == 1
    assert active_entries[0]["receiver_id"] == "mock:0"

    stop = await client.post("/api/receivers/mock:0/recording/stop")
    assert stop.status_code == 200
    assert stop.json()["data"]["active"] is False
    assert stop.json()["data"]["duration_seconds"] > 0

    filename = stop.json()["data"]["filename"]
    download = await client.get(f"/api/recordings/{filename}/download")
    assert download.status_code == 200
    assert download.content[:4] == b"RIFF"  # WAV container magic bytes

    delete = await client.delete(f"/api/recordings/{filename}")
    assert delete.status_code == 200

    listing_after = await client.get("/api/recordings")
    assert filename not in [r["filename"] for r in listing_after.json()["data"]]


async def test_iq_recording_lifecycle_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "iq"})
    assert start.status_code == 200
    assert start.json()["data"]["mode"] == "iq"

    await asyncio.sleep(0.3)

    stop = await client.post("/api/receivers/mock:0/recording/stop")
    assert stop.status_code == 200
    assert stop.json()["data"]["duration_seconds"] > 0

    filename = stop.json()["data"]["filename"]
    assert filename.endswith(".iq")

    download = await client.get(f"/api/recordings/{filename}/download")
    assert download.status_code == 200
    assert len(download.content) > 0

    await client.delete(f"/api/recordings/{filename}")


async def test_deleting_active_recording_conflicts(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "fm"})
    filename = start.json()["data"]["filename"]
    try:
        resp = await client.delete(f"/api/recordings/{filename}")
        assert resp.status_code == 409
    finally:
        await client.post("/api/receivers/mock:0/recording/stop")
        await client.delete(f"/api/recordings/{filename}")


async def test_deleting_unknown_recording_404s(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.delete("/api/recordings/does-not-exist.wav")
    assert resp.status_code == 404


async def test_deleting_recording_rejects_path_traversal(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.delete("/api/recordings/..%2F..%2Fconftest.py")
    assert resp.status_code == 404


async def test_starting_recording_twice_conflicts(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    first = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "fm"})
    assert first.status_code == 200
    try:
        second = await client.post("/api/receivers/mock:0/recording/start", json={"mode": "fm"})
        assert second.status_code == 409
    finally:
        await client.post("/api/receivers/mock:0/recording/stop")


async def test_stopping_unknown_recording_404s(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post("/api/receivers/mock:0/recording/stop")
    assert resp.status_code == 404


async def test_recordings_require_auth(client):
    resp = await client.get("/api/recordings")
    assert resp.status_code == 401
