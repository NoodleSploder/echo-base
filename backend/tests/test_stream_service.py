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


def _build_ax25_ui_frame(dest: str, src: str, info: bytes) -> bytes:
    from app.services.decoders.ax25 import compute_fcs

    def encode_address(callsign: str, is_last: bool) -> bytes:
        padded = callsign.upper().ljust(6)[:6]
        address = bytearray(ord(c) << 1 for c in padded)
        address.append(0x60 | (0x01 if is_last else 0))
        return bytes(address)

    payload = bytearray()
    payload += encode_address(dest, is_last=False)
    payload += encode_address(src, is_last=True)
    payload.append(0x03)  # UI frame control
    payload.append(0xF0)  # no layer-3 protocol
    payload += info
    fcs = compute_fcs(bytes(payload))
    payload.append(fcs & 0xFF)
    payload.append((fcs >> 8) & 0xFF)
    return bytes(payload)


async def test_aprs_packet_event_includes_position_when_present():
    """Exercises _decode_aprs directly with a stub decoder returning a
    real AX.25 frame carrying an APRS position report, bypassing the
    AFSK demod itself (already covered by test_afsk_decoder.py's round
    trip) to check the emitted event's lat/lon enrichment end to end."""
    frame_bytes = _build_ax25_ui_frame("APRS", "N0CALL", b"!4903.50N/07201.75W-Test 001234")

    class _StubDecoder:
        def feed(self, audio):
            return [frame_bytes]

    emitted = []

    class _StubEventBus:
        def emit(self, event_type, source, data):
            emitted.append((event_type, source, data))

    capture = _ReceiverCapture("test:0", open_handle=None, loop=None, event_bus=_StubEventBus())
    capture._aprs_decoder = _StubDecoder()

    capture._decode_aprs(np.zeros(10, dtype=np.complex64), decimation=5)

    assert len(emitted) == 1
    event_type, source, data = emitted[0]
    assert event_type == "AprsPacket"
    assert data["latitude"] == pytest.approx(49.05833, abs=1e-4)
    assert data["longitude"] == pytest.approx(-72.02917, abs=1e-4)
    assert data["symbol"] == "/-"


async def test_aprs_packet_event_omits_position_for_non_position_info():
    frame_bytes = _build_ax25_ui_frame("APRS", "N0CALL", b">Just a status message")

    class _StubDecoder:
        def feed(self, audio):
            return [frame_bytes]

    emitted = []

    class _StubEventBus:
        def emit(self, event_type, source, data):
            emitted.append((event_type, source, data))

    capture = _ReceiverCapture("test:0", open_handle=None, loop=None, event_bus=_StubEventBus())
    capture._aprs_decoder = _StubDecoder()

    capture._decode_aprs(np.zeros(10, dtype=np.complex64), decimation=5)

    assert len(emitted) == 1
    assert "latitude" not in emitted[0][2]


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


async def test_enable_signal_detection_starts_and_stops_capture(client):
    stream_service = app.state.stream_service

    await stream_service.enable_signal_detection("mock:0", margin_db=15.0, center_frequency_hz=None)
    assert "mock:0" in stream_service._captures

    await asyncio.sleep(0.2)  # should run its detection loop over noise without crashing
    assert "mock:0" in stream_service._captures

    await stream_service.disable_signal_detection("mock:0")
    assert "mock:0" not in stream_service._captures


async def test_signal_detection_and_spectrum_share_one_capture(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_spectrum("mock:0")
    await stream_service.enable_signal_detection("mock:0", margin_db=15.0, center_frequency_hz=None)
    try:
        assert len(stream_service._captures) == 1
    finally:
        await stream_service.disable_signal_detection("mock:0")
        assert "mock:0" in stream_service._captures  # spectrum subscriber keeps it alive
        await stream_service.unsubscribe_spectrum("mock:0", queue)

    assert "mock:0" not in stream_service._captures


async def test_signal_detected_event_reports_absolute_frequency():
    """Exercises _detect_signals directly with a controlled synthetic
    spectrum (the mock plugin's IQ is random noise, unsuitable for
    asserting a specific peak/frequency), checking bin-to-frequency math
    and event emission end to end."""
    import numpy as np

    capture = _ReceiverCapture("test:0", open_handle=None, loop=None, event_bus=None)
    emitted = []

    class _StubEventBus:
        def emit(self, event_type, source, data):
            emitted.append((event_type, source, data))

    capture._event_bus = _StubEventBus()
    capture.enable_signal_detection(margin_db=30.0, center_frequency_hz=100_000_000)

    fft_size = 64
    magnitude_db = np.full(fft_size, -80.0, dtype=np.float32)
    magnitude_db[40] = -10.0  # a clear peak, 8 bins above center (32)

    capture._detect_signals(magnitude_db, sample_rate_hz=240_000)

    assert len(emitted) == 1
    event_type, source, data = emitted[0]
    assert event_type == "SignalDetected"
    assert source == "test:0"
    assert data["power_db"] == pytest.approx(-10.0)
    expected_offset = (40 - fft_size / 2) * 240_000 / fft_size
    assert data["frequency_offset_hz"] == pytest.approx(expected_offset)
    assert data["frequency_hz"] == pytest.approx(100_000_000 + expected_offset)

    # A second frame with the same peak (even drifted a bin) shouldn't re-trigger.
    magnitude_db2 = magnitude_db.copy()
    capture._detect_signals(magnitude_db2, sample_rate_hz=240_000)
    assert len(emitted) == 1


async def test_enable_occupancy_starts_and_stops_capture(client):
    stream_service = app.state.stream_service

    await stream_service.enable_occupancy("mock:0", margin_db=15.0, center_frequency_hz=None)
    assert "mock:0" in stream_service._captures

    await asyncio.sleep(0.2)  # should run its occupancy loop over noise without crashing
    assert "mock:0" in stream_service._captures

    await stream_service.disable_occupancy("mock:0")
    assert "mock:0" not in stream_service._captures


async def test_get_occupancy_returns_none_when_not_enabled(client):
    stream_service = app.state.stream_service
    assert stream_service.get_occupancy("mock:0") is None


async def test_get_occupancy_returns_snapshot_once_enabled(client):
    stream_service = app.state.stream_service

    await stream_service.enable_occupancy("mock:0", margin_db=15.0, center_frequency_hz=100_000_000)
    try:
        await asyncio.sleep(0.2)  # let at least one frame get recorded
        snapshot = stream_service.get_occupancy("mock:0")
        assert snapshot is not None
        assert len(snapshot["frequencies_hz"]) == len(snapshot["occupancy_percent"])
        assert len(snapshot["frequencies_hz"]) > 0
    finally:
        await stream_service.disable_occupancy("mock:0")


async def test_occupancy_and_spectrum_share_one_capture(client):
    stream_service = app.state.stream_service

    queue = await stream_service.subscribe_spectrum("mock:0")
    await stream_service.enable_occupancy("mock:0", margin_db=15.0, center_frequency_hz=None)
    try:
        assert len(stream_service._captures) == 1
    finally:
        await stream_service.disable_occupancy("mock:0")
        assert "mock:0" in stream_service._captures  # spectrum subscriber keeps it alive
        await stream_service.unsubscribe_spectrum("mock:0", queue)

    assert "mock:0" not in stream_service._captures
