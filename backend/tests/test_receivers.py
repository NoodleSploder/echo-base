import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def test_list_receivers_includes_mock(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/receivers")
    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()["data"]]
    assert "mock:0" in ids


async def test_receiver_lifecycle(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/start")
    assert start.status_code == 200
    assert start.json()["data"]["state"] == "streaming"

    tune = await client.post("/api/receivers/mock:0/tune", json={"frequency": 144390000})
    assert tune.status_code == 200
    assert tune.json()["data"]["frequency_hz"] == 144390000

    stop = await client.post("/api/receivers/mock:0/stop")
    assert stop.status_code == 200
    assert stop.json()["data"]["state"] == "idle"


async def test_ppm_correction_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post("/api/receivers/mock:0/ppm-correction", json={"ppm": 12})
    assert resp.status_code == 200
    assert resp.json()["data"]["ppm_correction"] == 12

    status = await client.get("/api/receivers/mock:0")
    assert status.json()["data"]["ppm_correction"] == 12


async def test_ads_b_start_stop_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/ads-b/start")
    assert start.status_code == 200

    # Confirms ADS-B decoding actually runs against a real capture loop
    # (the mock plugin's random-noise IQ) without crashing, for a bit
    # longer than a single event-loop tick.
    await asyncio.sleep(0.3)

    health = await client.get("/api/receivers/mock:0/capture-health")
    assert health.json()["data"]["ads_b_enabled"] is True

    stop = await client.post("/api/receivers/mock:0/ads-b/stop")
    assert stop.status_code == 200


async def test_ais_start_stop_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/ais/start")
    assert start.status_code == 200

    await asyncio.sleep(0.3)

    health = await client.get("/api/receivers/mock:0/capture-health")
    assert health.json()["data"]["ais_enabled"] is True

    stop = await client.post("/api/receivers/mock:0/ais/stop")
    assert stop.status_code == 200


async def test_sstv_start_stop_and_query_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/sstv/start")
    assert start.status_code == 200

    await asyncio.sleep(0.3)  # let at least one frame get fed to the decoder

    snapshot = await client.get("/api/receivers/mock:0/sstv")
    assert snapshot.status_code == 200
    data = snapshot.json()["data"]
    assert data["total_lines"] == 256
    assert "lines_decoded" in data
    assert "is_complete" in data

    image = await client.get("/api/receivers/mock:0/sstv/image.png")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content[:8] == b"\x89PNG\r\n\x1a\n"  # real PNG magic bytes, not an empty/error body

    stop = await client.post("/api/receivers/mock:0/sstv/stop")
    assert stop.status_code == 200

    after_stop = await client.get("/api/receivers/mock:0/sstv")
    assert after_stop.status_code == 422


async def test_ft8_start_stop_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/ft8/start")
    assert start.status_code == 200

    await asyncio.sleep(0.3)

    health = await client.get("/api/receivers/mock:0/capture-health")
    assert health.json()["data"]["ft8_enabled"] is True

    stop = await client.post("/api/receivers/mock:0/ft8/stop")
    assert stop.status_code == 200


async def test_status_reflects_real_capture_without_start(client, admin_user):
    """A spectrum/audio subscriber makes IQ actually flow even if the
    user never clicked Start -- the reported state should say so."""
    await client.post("/api/auth/login", json=admin_user)

    from app.main import app

    idle = await client.get("/api/receivers/mock:0")
    assert idle.json()["data"]["state"] == "idle"

    stream_service = app.state.stream_service
    queue = await stream_service.subscribe_spectrum("mock:0")
    try:
        active = await client.get("/api/receivers/mock:0")
        assert active.json()["data"]["state"] == "streaming"
    finally:
        await stream_service.unsubscribe_spectrum("mock:0", queue)

    idle_again = await client.get("/api/receivers/mock:0")
    assert idle_again.json()["data"]["state"] == "idle"


async def test_signal_detection_start_stop_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post(
        "/api/receivers/mock:0/signal-detection/start", json={"margin_db": 15.0}
    )
    assert start.status_code == 200

    active = await client.get("/api/receivers/mock:0")
    assert active.json()["data"]["state"] == "streaming"

    stop = await client.post("/api/receivers/mock:0/signal-detection/stop")
    assert stop.status_code == 200

    idle = await client.get("/api/receivers/mock:0")
    assert idle.json()["data"]["state"] == "idle"


async def test_signal_detection_start_unknown_receiver_404s(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post(
        "/api/receivers/does-not-exist/signal-detection/start", json={"margin_db": 15.0}
    )
    assert resp.status_code == 404


async def test_occupancy_start_stop_and_query_via_rest(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    start = await client.post("/api/receivers/mock:0/occupancy/start", json={"margin_db": 15.0})
    assert start.status_code == 200

    await asyncio.sleep(0.2)  # let at least one frame get recorded

    snapshot = await client.get("/api/receivers/mock:0/occupancy")
    assert snapshot.status_code == 200
    data = snapshot.json()["data"]
    assert len(data["frequencies_hz"]) == len(data["occupancy_percent"])
    assert len(data["frequencies_hz"]) > 0

    stop = await client.post("/api/receivers/mock:0/occupancy/stop")
    assert stop.status_code == 200

    after_stop = await client.get("/api/receivers/mock:0/occupancy")
    assert after_stop.status_code == 422


async def test_occupancy_query_without_enabling_422s(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/receivers/mock:0/occupancy")
    assert resp.status_code == 422


async def test_unknown_receiver_returns_404(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/receivers/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RECEIVER_NOT_FOUND"


async def test_receivers_require_auth(client):
    resp = await client.get("/api/receivers")
    assert resp.status_code == 401
