import pytest

pytestmark = pytest.mark.asyncio


async def test_login_success_and_me(client, admin_user):
    resp = await client.post("/api/auth/login", json=admin_user)
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["username"] == "admin"
    assert body["role"] == "administrator"
    assert "echo_base_session" in resp.cookies

    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "admin"


async def test_login_invalid_password(client, admin_user):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_logout_clears_session(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 200

    me = await client.get("/api/auth/me")
    assert me.status_code == 401
