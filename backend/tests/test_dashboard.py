import pytest

pytestmark = pytest.mark.asyncio


async def test_layout_defaults_to_none(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/dashboard/layout")
    assert resp.status_code == 200
    assert resp.json()["data"]["layout"] is None


async def test_layout_round_trip(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    layout = {"lg": [{"i": "receivers", "x": 0, "y": 0, "w": 4, "h": 6}]}
    save = await client.put("/api/dashboard/layout", json={"layout": layout})
    assert save.status_code == 200

    resp = await client.get("/api/dashboard/layout")
    assert resp.status_code == 200
    assert resp.json()["data"]["layout"] == layout


async def test_layout_requires_auth(client):
    resp = await client.get("/api/dashboard/layout")
    assert resp.status_code == 401
