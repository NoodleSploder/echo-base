"""Spectrum scan: cycles a receiver through a frequency list on a
timer, actually retuning the real (mock) receiver each dwell period,
and stops cleanly.
"""
from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.asyncio


async def test_scan_cycles_real_tuning(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post(
        "/api/receivers/mock:0/scan/start",
        json={"frequencies": [100000000, 200000000, 300000000], "dwell_seconds": 0.2},
    )
    assert resp.status_code == 200

    receiver_service = app.state.receiver_service
    seen_frequencies = set()
    for _ in range(30):
        status = await receiver_service.status("mock:0")
        seen_frequencies.add(status.frequency_hz)
        if len(seen_frequencies) == 3:
            break
        await asyncio.sleep(0.15)

    assert seen_frequencies == {100000000, 200000000, 300000000}

    stop = await client.post("/api/receivers/mock:0/scan/stop")
    assert stop.status_code == 200

    status_resp = await client.get("/api/receivers/mock:0/scan/status")
    assert status_resp.json()["data"]["active"] is False


async def test_scan_status_reports_current_frequency(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    await client.post(
        "/api/receivers/mock:0/scan/start",
        json={"frequencies": [123000000, 456000000], "dwell_seconds": 5},
    )
    status_resp = await client.get("/api/receivers/mock:0/scan/status")
    body = status_resp.json()["data"]
    assert body["active"] is True
    assert body["current_frequency_hz"] == 123000000
    assert body["frequencies"] == [123000000, 456000000]

    await client.post("/api/receivers/mock:0/scan/stop")


async def test_scan_rejects_empty_frequency_list(client, admin_user):
    await client.post("/api/auth/login", json=admin_user)

    resp = await client.post("/api/receivers/mock:0/scan/start", json={"frequencies": []})
    assert resp.status_code == 422


async def test_scan_requires_auth(client):
    resp = await client.post(
        "/api/receivers/mock:0/scan/start", json={"frequencies": [100000000]}
    )
    assert resp.status_code == 401
