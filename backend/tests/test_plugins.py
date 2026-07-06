import pytest

pytestmark = pytest.mark.asyncio


async def test_list_plugins(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/plugins")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()["data"]]
    assert "mock_receiver" in ids


async def test_disable_and_enable_plugin(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    disable = await client.post("/api/plugins/mock_receiver/disable")
    assert disable.status_code == 200
    assert disable.json()["data"]["enabled"] is False

    # A disabled receiver plugin should disappear from the Receiver Manager.
    receivers = await client.get("/api/receivers")
    assert "mock:0" not in [r["id"] for r in receivers.json()["data"]]

    enable = await client.post("/api/plugins/mock_receiver/enable")
    assert enable.status_code == 200
    assert enable.json()["data"]["enabled"] is True


async def test_unknown_plugin_returns_404(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/plugins/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PLUGIN_NOT_FOUND"
