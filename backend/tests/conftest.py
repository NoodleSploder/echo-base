"""Pytest configuration.

Environment variables that steer app configuration must be set before
`app.main` is imported anywhere (including transitively via other
fixtures), since `app.main` builds a module-level FastAPI app at import
time. Everything at module scope here runs before pytest starts
collecting test modules in this directory.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="echo_base_test_"))
_PLUGINS_DIR = _TEST_ROOT / "plugins"
_MOCK_PLUGIN_DIR = _PLUGINS_DIR / "mock_receiver"
_MOCK_PLUGIN_DIR.mkdir(parents=True)

(_MOCK_PLUGIN_DIR / "manifest.yaml").write_text(
    "name: Mock Receiver\n"
    "id: mock_receiver\n"
    "version: 0.1.0\n"
    "plugin_type: receiver\n"
    "entry_point: plugin.py\n"
)

(_MOCK_PLUGIN_DIR / "plugin.py").write_text(
    '''
"""In-memory receiver plugin used only by the backend test suite."""
import os

from app.plugins import ReceiverDescriptor, ReceiverPlugin, ReceiverStatus


class MockIqStream:
    """Deterministic-enough fake IQ source so StreamService can be tested
    without real SDR hardware."""

    def __init__(self, sample_rate_hz):
        self.sample_rate_hz = sample_rate_hz
        self._closed = False

    def read(self, n):
        if self._closed:
            return b""
        return os.urandom(n)

    def close(self):
        self._closed = True


class MockReceiverPlugin(ReceiverPlugin):
    def initialize(self) -> None:
        self._state = {
            "state": "idle",
            "frequency_hz": None,
            "gain": "auto",
            "bandwidth_hz": None,
            "sample_rate_hz": 2_048_000,
        }

    def discover(self):
        return [ReceiverDescriptor(id="mock:0", name="Mock Receiver 0", driver="mock_receiver")]

    def start(self, receiver_id):
        self._state["state"] = "streaming"
        return self.device_status(receiver_id)

    def stop(self, receiver_id):
        self._state["state"] = "idle"
        return self.device_status(receiver_id)

    def tune(self, receiver_id, frequency_hz):
        self._state["frequency_hz"] = frequency_hz
        return self.device_status(receiver_id)

    def set_gain(self, receiver_id, gain):
        self._state["gain"] = gain
        return self.device_status(receiver_id)

    def set_bandwidth(self, receiver_id, bandwidth_hz):
        self._state["bandwidth_hz"] = bandwidth_hz
        return self.device_status(receiver_id)

    def set_sample_rate(self, receiver_id, sample_rate_hz):
        self._state["sample_rate_hz"] = sample_rate_hz
        return self.device_status(receiver_id)

    def device_status(self, receiver_id):
        return ReceiverStatus(id=receiver_id, **self._state)

    def open_iq_stream(self, receiver_id):
        return MockIqStream(self._state["sample_rate_hz"] or 240_000)
'''
)

os.environ["ECHO_BASE_ENVIRONMENT"] = "testing"
os.environ["ECHO_BASE_CONFIG_FILE"] = str(_TEST_ROOT / "unused.yaml")
os.environ["ECHO_BASE_LOGGING__DIRECTORY"] = str(_TEST_ROOT / "logs")
os.environ["ECHO_BASE_PLUGINS__DIRECTORY"] = str(_PLUGINS_DIR)
os.environ["ECHO_BASE_RECORDINGS__DIRECTORY"] = str(_TEST_ROOT / "recordings")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models.user import User, UserRole  # noqa: E402
from app.db.session import get_session_factory  # noqa: E402
from app.main import app  # noqa: E402


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)


@pytest_asyncio.fixture
async def client(tmp_path):
    os.environ["ECHO_BASE_DATABASE__URL"] = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    get_settings.cache_clear()

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


ADMIN_PASSWORD = "test-password-123"


@pytest_asyncio.fixture
async def admin_user(client):
    """Replace the auto-bootstrapped admin with one whose password we know."""
    factory = get_session_factory()
    async with factory() as db:
        await db.execute(delete(User))
        db.add(
            User(
                username="admin",
                hashed_password=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMINISTRATOR,
            )
        )
        await db.commit()
    return {"username": "admin", "password": ADMIN_PASSWORD}
