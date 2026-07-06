import asyncio

import numpy as np
import pytest

from app.main import app
from app.services.stream_service import OUTPUT_BINS, _ReceiverCapture

pytestmark = pytest.mark.asyncio


async def test_subscribe_spectrum_yields_fft_frames_of_expected_size(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_spectrum("mock:0")
    try:
        frame = await asyncio.wait_for(queue.get(), timeout=5)
    finally:
        await stream_service.unsubscribe_spectrum("mock:0", queue)

    assert len(frame) == OUTPUT_BINS * 4  # float32 magnitudes in dB


async def test_subscribe_audio_yields_pcm_chunks(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_audio("mock:0", "fm")
    try:
        chunk = await asyncio.wait_for(queue.get(), timeout=5)
    finally:
        await stream_service.unsubscribe_audio("mock:0", "fm", queue)

    assert len(chunk) > 0


async def test_subscribe_iq_yields_raw_bytes(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_iq("mock:0")
    try:
        chunk = await asyncio.wait_for(queue.get(), timeout=5)
        assert len(chunk) > 0
        assert len(chunk) % 2 == 0  # interleaved I/Q pairs
        assert stream_service.get_sample_rate("mock:0") is not None
    finally:
        await stream_service.unsubscribe_iq("mock:0", queue)

    assert "mock:0" not in stream_service._captures


async def test_iq_and_spectrum_share_one_capture(client):
    stream_service = app.state.stream_service

    spectrum_queue = await stream_service.subscribe_spectrum("mock:0")
    iq_queue = await stream_service.subscribe_iq("mock:0")
    try:
        assert len(stream_service._captures) == 1
    finally:
        await stream_service.unsubscribe_spectrum("mock:0", spectrum_queue)
        assert "mock:0" in stream_service._captures  # IQ subscriber keeps it alive
        await stream_service.unsubscribe_iq("mock:0", iq_queue)

    assert "mock:0" not in stream_service._captures


async def test_spectrum_and_audio_share_one_capture(client):
    """The whole point of unifying: watching spectrum and listening to
    audio on the same receiver must not open two competing captures."""
    stream_service = app.state.stream_service

    spectrum_queue = await stream_service.subscribe_spectrum("mock:0")
    audio_queue = await stream_service.subscribe_audio("mock:0", "fm")
    try:
        assert len(stream_service._captures) == 1
        await asyncio.wait_for(spectrum_queue.get(), timeout=5)
        await asyncio.wait_for(audio_queue.get(), timeout=5)
    finally:
        await stream_service.unsubscribe_spectrum("mock:0", spectrum_queue)
        # Capture must stay alive for the remaining audio subscriber.
        assert "mock:0" in stream_service._captures
        await stream_service.unsubscribe_audio("mock:0", "fm", audio_queue)

    assert "mock:0" not in stream_service._captures


async def test_unsubscribe_last_subscriber_stops_capture(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_spectrum("mock:0")
    assert "mock:0" in stream_service._captures

    await stream_service.unsubscribe_spectrum("mock:0", queue)
    assert "mock:0" not in stream_service._captures


async def test_subscribe_spectrum_unknown_receiver_raises(client):
    from app.services.receiver_service import ReceiverNotFoundError

    stream_service = app.state.stream_service
    with pytest.raises(ReceiverNotFoundError):
        await stream_service.subscribe_spectrum("does-not-exist")


async def test_subscribe_audio_unknown_receiver_raises(client):
    from app.services.receiver_service import ReceiverNotFoundError

    stream_service = app.state.stream_service
    with pytest.raises(ReceiverNotFoundError):
        await stream_service.subscribe_audio("does-not-exist", "fm")


async def test_enable_aprs_starts_and_stops_capture(client):
    stream_service = app.state.stream_service

    await stream_service.enable_aprs("mock:0")
    assert "mock:0" in stream_service._captures

    # Give the capture thread a moment to run its decode loop at least
    # once over the mock plugin's random IQ -- it shouldn't crash even
    # though random noise never contains a valid AX.25 frame.
    await asyncio.sleep(0.2)
    assert "mock:0" in stream_service._captures

    await stream_service.disable_aprs("mock:0")
    assert "mock:0" not in stream_service._captures


async def test_aprs_and_spectrum_share_one_capture(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_spectrum("mock:0")
    await stream_service.enable_aprs("mock:0")
    try:
        assert len(stream_service._captures) == 1
    finally:
        await stream_service.disable_aprs("mock:0")
        assert "mock:0" in stream_service._captures  # spectrum subscriber keeps it alive
        await stream_service.unsubscribe_spectrum("mock:0", queue)

    assert "mock:0" not in stream_service._captures


async def test_enable_same_starts_and_stops_capture(client):
    stream_service = app.state.stream_service

    await stream_service.enable_same("mock:0")
    assert "mock:0" in stream_service._captures

    await asyncio.sleep(0.2)  # decode loop should run at least once, no crash
    assert "mock:0" in stream_service._captures

    await stream_service.disable_same("mock:0")
    assert "mock:0" not in stream_service._captures


async def test_same_alert_event_includes_human_readable_fields():
    """Exercises _decode_same directly with a stub decoder returning a
    known header, bypassing the FSK demod itself (already covered by
    test_same_decoder.py's round trip) to check the emitted event's
    enrichment (describe_event/describe_location) end to end."""

    class _StubDecoder:
        def feed(self, audio):
            return ["ZCZC-WXR-TOR-006037+0030-1231423-KLOX/NWS-"]

    emitted = []

    class _StubEventBus:
        def emit(self, event_type, source, data):
            emitted.append((event_type, source, data))

    capture = _ReceiverCapture("test:0", open_handle=None, loop=None, event_bus=_StubEventBus())
    capture._same_decoder = _StubDecoder()

    capture._decode_same(np.zeros(10, dtype=np.complex64), decimation=5)

    assert len(emitted) == 1
    event_type, source, data = emitted[0]
    assert event_type == "SameAlert"
    assert source == "test:0"
    assert data["event_name"] == "Tornado Warning"
    assert data["location_names"] == ["County 037, California"]


async def test_aprs_and_same_share_one_capture(client):
    stream_service = app.state.stream_service

    await stream_service.enable_aprs("mock:0")
    await stream_service.enable_same("mock:0")
    try:
        assert len(stream_service._captures) == 1
    finally:
        await stream_service.disable_aprs("mock:0")
        assert "mock:0" in stream_service._captures  # SAME decoding keeps it alive
        await stream_service.disable_same("mock:0")

    assert "mock:0" not in stream_service._captures
