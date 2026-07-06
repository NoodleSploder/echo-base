"""n2yo.com TLE client: parses a real-shaped response correctly, and
surfaces n2yo's own quirks (HTTP 200 with an empty/malformed body for
some bad requests, rather than a clean error status) as a real error
instead of silently returning garbage.

No live network call/API key needed -- httpx.MockTransport stands in
for n2yo.com's actual HTTP responses (whose documented shape is what's
being tested against here, not live behavior this environment can't
authenticate to without a registered account).
"""
from __future__ import annotations

import httpx
import pytest

from app.services.n2yo import N2yoError, fetch_tle

pytestmark = pytest.mark.asyncio


def _mock_client(handler):
    real_async_client = httpx.AsyncClient

    def _patched_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    return _patched_client


async def test_fetch_tle_parses_real_shaped_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["apiKey"] == "test-key"
        assert request.url.path.endswith("/tle/25338")
        return httpx.Response(
            200,
            json={
                "info": {"satid": 25338, "satname": "NOAA 15", "transactionscount": 1},
                "tle": (
                    "1 25338U 98030A   26187.25559808  .00000133  00000+0  71966-4 0  9996\r\n"
                    "2 25338  98.5062 207.3726 0009082 294.5375  65.4859 14.27152357464013"
                ),
            },
        )

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    name, tle1, tle2 = await fetch_tle(25338, "test-key")
    assert name == "NOAA 15"
    assert tle1.startswith("1 25338U")
    assert tle2.startswith("2 25338")


async def test_fetch_tle_raises_on_unknown_norad_id(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"info": {"satid": 99999999, "transactionscount": 0}})

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    with pytest.raises(N2yoError):
        await fetch_tle(99999999, "test-key")


async def test_fetch_tle_raises_on_non_json_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    with pytest.raises(N2yoError):
        await fetch_tle(25338, "test-key")


async def test_fetch_tle_raises_on_http_error_status(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "invalid key"})

    monkeypatch.setattr(httpx, "AsyncClient", _mock_client(handler))

    with pytest.raises(N2yoError):
        await fetch_tle(25338, "bad-key")


async def test_tle_route_400s_without_configured_api_key(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.get("/api/satellites/tle/25338")
    assert resp.status_code == 422


async def test_tle_route_returns_tle_when_configured(client, admin_user, monkeypatch):
    from app.main import app

    app.state.settings.satellites.n2yo_api_key = "test-key"
    try:

        async def fake_fetch_tle(norad_id, api_key):
            assert norad_id == 25338
            assert api_key == "test-key"
            return ("NOAA 15", "1 25338U ...", "2 25338 ...")

        monkeypatch.setattr("app.api.routes.satellites.fetch_tle", fake_fetch_tle)

        await client.post("/api/auth/login", json=admin_user)
        resp = await client.get("/api/satellites/tle/25338")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["name"] == "NOAA 15"
        assert body["tle_line1"] == "1 25338U ..."
    finally:
        app.state.settings.satellites.n2yo_api_key = None
