import asyncio

import pytest

from app.main import app
from app.services.spectrum_service import OUTPUT_BINS

pytestmark = pytest.mark.asyncio


async def test_subscribe_yields_fft_frames_of_expected_size(client):
    spectrum_service = app.state.spectrum_service

    queue = await spectrum_service.subscribe("mock:0")
    try:
        frame = await asyncio.wait_for(queue.get(), timeout=5)
    finally:
        await spectrum_service.unsubscribe("mock:0", queue)

    assert len(frame) == OUTPUT_BINS * 4  # float32 magnitudes in dB


async def test_unsubscribe_last_subscriber_stops_worker(client):
    spectrum_service = app.state.spectrum_service

    queue = await spectrum_service.subscribe("mock:0")
    assert "mock:0" in spectrum_service._workers

    await spectrum_service.unsubscribe("mock:0", queue)
    assert "mock:0" not in spectrum_service._workers


async def test_subscribe_unknown_receiver_raises(client):
    from app.services.receiver_service import ReceiverNotFoundError

    spectrum_service = app.state.spectrum_service
    with pytest.raises(ReceiverNotFoundError):
        await spectrum_service.subscribe("does-not-exist")
