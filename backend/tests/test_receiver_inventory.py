"""Receiver inventory: upsert-on-seen persists across "disappearing"
(no second row, first_seen_at preserved, last_seen_at refreshed), and
survives independently of whatever's currently attached -- exercised
directly against the service, then via the real HotplugMonitor/REST
path against the mock plugin.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.plugins.receiver import ReceiverDescriptor
from app.services.receiver_inventory import list_inventory, upsert_seen

pytestmark = pytest.mark.asyncio


async def test_upsert_seen_creates_then_updates(client):
    # The app's own HotplugMonitor already seeded "mock:0" at startup
    # (real behavior) -- use a receiver_id it doesn't know about so
    # this test's own row count assertions aren't affected by that.
    descriptor = ReceiverDescriptor(id="rtl_sdr:1", name="RTL-SDR #1", driver="rtl_sdr", serial="1")
    first_seen = datetime(2026, 1, 1, tzinfo=UTC)
    await upsert_seen(descriptor, seen_at=first_seen)

    def _matching(records):
        return [r for r in records if r.receiver_id == "rtl_sdr:1"]

    # SQLite round-trips DateTime columns as naive -- compare on the
    # naive wall-clock value, same as other tests in this suite that
    # touch timestamp columns.
    records = _matching(await list_inventory())
    assert len(records) == 1
    assert records[0].first_seen_at == first_seen.replace(tzinfo=None)
    assert records[0].last_seen_at == first_seen.replace(tzinfo=None)

    later = first_seen + timedelta(days=1)
    await upsert_seen(descriptor, seen_at=later)

    records = _matching(await list_inventory())
    assert len(records) == 1  # updated in place, not a second row
    assert records[0].first_seen_at == first_seen.replace(tzinfo=None)
    assert records[0].last_seen_at == later.replace(tzinfo=None)


async def test_inventory_via_rest_reflects_hotplug_monitor(client, admin_user):
    from app.main import app

    await client.post("/api/auth/login", json=admin_user)

    hotplug_monitor = app.state.hotplug_monitor
    # start() already seeded from the mock plugin's fixed "mock:0"
    # receiver at app startup; force another poll for a deterministic
    # point to assert against instead of racing the real timer.
    await hotplug_monitor.check_once()

    resp = await client.get("/api/receivers/inventory")
    assert resp.status_code == 200
    records = resp.json()["data"]
    mock_record = next(r for r in records if r["receiver_id"] == "mock:0")
    assert mock_record["attached"] is True
    assert mock_record["driver"] == "mock_receiver"


async def test_inventory_requires_auth(client):
    resp = await client.get("/api/receivers/inventory")
    assert resp.status_code == 401
