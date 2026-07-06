import pytest

pytestmark = pytest.mark.asyncio


async def test_health_is_public(client):
    resp = await client.get("/api/system/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "connected"


async def test_system_info_requires_auth(client):
    resp = await client.get("/api/system")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHENTICATED"
