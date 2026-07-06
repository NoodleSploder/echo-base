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


async def test_unknown_receiver_returns_404(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/receivers/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RECEIVER_NOT_FOUND"


async def test_receivers_require_auth(client):
    resp = await client.get("/api/receivers")
    assert resp.status_code == 401
