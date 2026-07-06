import pytest

pytestmark = pytest.mark.asyncio


async def test_profile_crud_round_trip(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    create = await client.post(
        "/api/receiver-profiles",
        json={"name": "2m Calling", "frequency_hz": 146520000, "gain": "auto"},
    )
    assert create.status_code == 200
    profile = create.json()["data"]
    assert profile["name"] == "2m Calling"
    profile_id = profile["id"]

    listing = await client.get("/api/receiver-profiles")
    assert listing.status_code == 200
    assert [p["id"] for p in listing.json()["data"]] == [profile_id]

    update = await client.put(
        f"/api/receiver-profiles/{profile_id}",
        json={"name": "2m Calling", "frequency_hz": 146520000, "gain": "40"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["gain"] == "40"

    delete = await client.delete(f"/api/receiver-profiles/{profile_id}")
    assert delete.status_code == 200

    listing_after = await client.get("/api/receiver-profiles")
    assert listing_after.json()["data"] == []


async def test_unknown_profile_returns_404(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.put(
        "/api/receiver-profiles/does-not-exist",
        json={"name": "x", "frequency_hz": 1},
    )
    assert resp.status_code == 404


async def test_apply_profile_tunes_receiver(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    create = await client.post(
        "/api/receiver-profiles",
        json={"name": "FT8 20m", "frequency_hz": 14074000, "gain": "auto"},
    )
    profile_id = create.json()["data"]["id"]

    apply = await client.post(f"/api/receiver-profiles/{profile_id}/apply/mock:0")
    assert apply.status_code == 200
    assert apply.json()["data"]["frequency_hz"] == 14074000


async def test_apply_profile_with_margin_db_enables_signal_detection(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    create = await client.post(
        "/api/receiver-profiles",
        json={"name": "FM Broadcast", "frequency_hz": 100300000, "gain": "auto", "margin_db": 12.0},
    )
    profile_id = create.json()["data"]["id"]

    health_before = await client.get("/api/receivers/mock:0/capture-health")
    assert health_before.json()["data"].get("signal_detection_enabled") in (None, False)

    apply = await client.post(f"/api/receiver-profiles/{profile_id}/apply/mock:0")
    assert apply.status_code == 200

    health_after = await client.get("/api/receivers/mock:0/capture-health")
    assert health_after.json()["data"]["signal_detection_enabled"] is True

    from app.main import app

    await app.state.stream_service.disable_signal_detection("mock:0")


async def test_apply_profile_with_occupancy_margin_db_enables_occupancy(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    create = await client.post(
        "/api/receiver-profiles",
        json={
            "name": "FM Broadcast",
            "frequency_hz": 100300000,
            "gain": "auto",
            "occupancy_margin_db": 8.0,
        },
    )
    profile_id = create.json()["data"]["id"]
    assert create.json()["data"]["occupancy_margin_db"] == 8.0

    apply = await client.post(f"/api/receiver-profiles/{profile_id}/apply/mock:0")
    assert apply.status_code == 200

    health_after = await client.get("/api/receivers/mock:0/capture-health")
    assert health_after.json()["data"]["occupancy_enabled"] is True

    from app.main import app

    await app.state.stream_service.disable_occupancy("mock:0")


async def test_profiles_require_auth(client):
    resp = await client.get("/api/receiver-profiles")
    assert resp.status_code == 401
