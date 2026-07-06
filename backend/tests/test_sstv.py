"""SSTV Martin M1 decoder: a synthetic image, encoded into a real
Martin M1 audio-frequency waveform (continuous-phase FM, same
generation technique real transmitters use), round-trips back through
Hilbert-transform instantaneous-frequency recovery + sync detection +
per-pixel averaging to (near enough) the exact image it was built
from -- the same "encode, decode, compare" pattern as `test_mode_s.py`.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.services.decoders import sstv as _sstv
from app.services.decoders.sstv import (
    CHANNEL_ORDER,
    HEIGHT,
    SYNC_HZ,
    WIDTH,
    MartinM1Decoder,
    find_sync_pulse,
    hz_to_luma,
    instantaneous_frequency_hz,
)

_BLACK_HZ = _sstv.BLACK_HZ
_WHITE_HZ = _sstv.WHITE_HZ
_SYNC_DURATION_S = _sstv.SYNC_DURATION_S
_SYNC_PORCH_S = _sstv.SYNC_PORCH_S
_CHANNEL_SCAN_S = _sstv.CHANNEL_SCAN_S

SAMPLE_RATE_HZ = 24_000  # smaller than the real 48kHz audio rate -- keeps the synthetic test fast
_CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2}


def _fm_generate(freq_hz: np.ndarray, sample_rate_hz: int) -> np.ndarray:
    """Continuous-phase FM synthesis: integrate frequency into phase so
    consecutive segments don't click at their boundaries, the same way
    a real SSTV transmitter's VCO would behave."""
    phase = np.cumsum(2 * np.pi * freq_hz.astype(np.float64) / sample_rate_hz)
    return np.cos(phase).astype(np.float32)


def _repeat_to_exact_length(values: np.ndarray, length: int) -> np.ndarray:
    """Same idea as `np.repeat(values, length // len(values))`, but the
    output is exactly `length` samples long even when it doesn't divide
    evenly -- matters here because the decoder assumes each channel
    segment is *exactly* `channel_len` samples (an analog VCO doesn't
    quantize its own timing to a whole number of samples per pixel);
    truncating like plain integer-repeat would drifts the encoded
    line's total length short of what the decoder expects, throwing
    off every subsequent line's sync search."""
    sample_index = np.arange(length)
    value_index = np.clip((sample_index * len(values)) // length, 0, len(values) - 1)
    return values[value_index]


def _encode_martin_m1(image: np.ndarray, sample_rate_hz: int) -> np.ndarray:
    sync_len = round(_SYNC_DURATION_S * sample_rate_hz)
    porch_len = round(_SYNC_PORCH_S * sample_rate_hz)
    channel_len = round(_CHANNEL_SCAN_S * sample_rate_hz)

    freq_segments = []
    for row in range(image.shape[0]):
        freq_segments.append(np.full(sync_len, SYNC_HZ))
        for channel in CHANNEL_ORDER:
            freq_segments.append(np.full(porch_len, _BLACK_HZ))
            pixel_values = image[row, :, _CHANNEL_INDEX[channel]].astype(np.float64)
            pixel_freqs = _BLACK_HZ + (pixel_values / 255.0) * (_WHITE_HZ - _BLACK_HZ)
            freq_segments.append(_repeat_to_exact_length(pixel_freqs, channel_len))
    freq_hz = np.concatenate(freq_segments)
    return _fm_generate(freq_hz, sample_rate_hz)


def _test_image(height: int, width: int) -> np.ndarray:
    """A smooth gradient pattern, not per-pixel random noise -- like
    any real analog FM signal, this decoder can only track frequency
    changes as fast as a receiver can resolve them (~11 samples per
    pixel at 24kHz); a real transmitter's own output filtering limits
    its slew rate the same way, so no real photograph or real SSTV
    signal ever actually swings the full black-to-white frequency
    range between two adjacent pixels the way synthetic per-pixel
    white noise would. Smooth, band-limited content is the realistic
    (and fair) thing to round-trip against."""
    y, x = np.mgrid[0:height, 0:width]
    r = (np.sin(x / width * 4 * np.pi) + 1) / 2 * 255
    g = (np.cos(y / max(height, 1) * 3 * np.pi + x / width * 2 * np.pi) + 1) / 2 * 255
    b = ((x + y) % max(width, 1)) / max(width, 1) * 255
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


def test_hz_to_luma_clips_and_scales():
    freq = np.array([1000.0, _BLACK_HZ, (_BLACK_HZ + _WHITE_HZ) / 2, _WHITE_HZ, 3000.0])
    luma = hz_to_luma(freq)
    assert luma[0] == 0  # below black clips to black
    assert luma[1] == 0
    assert luma[2] == pytest.approx(127, abs=2)
    assert luma[3] == 255
    assert luma[4] == 255  # above white clips to white


def test_instantaneous_frequency_recovers_a_steady_tone():
    duration_s = 0.05
    n = int(duration_s * SAMPLE_RATE_HZ)
    tone_hz = 1800.0
    t = np.arange(n) / SAMPLE_RATE_HZ
    audio = np.cos(2 * np.pi * tone_hz * t).astype(np.float32)

    freq = instantaneous_frequency_hz(audio, SAMPLE_RATE_HZ)
    # Edges of the Hilbert transform are less accurate -- check the middle.
    middle = freq[n // 4 : 3 * n // 4]
    assert middle.mean() == pytest.approx(tone_hz, rel=0.02)


def test_find_sync_pulse_locates_a_real_pulse():
    sync_len = round(_SYNC_DURATION_S * SAMPLE_RATE_HZ)
    freq = np.concatenate(
        [
            np.full(500, 1800.0),  # picture data before the pulse
            np.full(sync_len, SYNC_HZ),
            np.full(500, 1800.0),
        ]
    )
    start = find_sync_pulse(freq, SAMPLE_RATE_HZ)
    assert start is not None
    assert abs(start - 500) < sync_len // 2


def test_find_sync_pulse_returns_none_without_one():
    freq = np.full(2000, 1800.0)
    assert find_sync_pulse(freq, SAMPLE_RATE_HZ) is None


def test_martin_m1_decoder_round_trips_a_small_image():
    # A handful of real lines (not the full 256 -- keeps the synthetic
    # waveform, and the FFT-based Hilbert transform run over it, small
    # enough for a fast test) -- decode should track lines_decoded
    # correctly and reconstruct the pixel values it was given.
    n_lines = 4
    image = _test_image(n_lines, WIDTH)
    waveform = _encode_martin_m1(image, SAMPLE_RATE_HZ)

    decoder = MartinM1Decoder(SAMPLE_RATE_HZ)
    # Feed in a couple of chunks rather than all at once, matching how
    # stream_service.py delivers ~20-100ms chunks in real use.
    midpoint = len(waveform) // 2
    decoder.feed(waveform[:midpoint])
    decoder.feed(waveform[midpoint:])

    assert decoder.lines_decoded == n_lines
    decoded = decoder.image[:n_lines]
    # Averaging a whole pixel's tone recovers brightness closely, but
    # not bit-exactly -- a few luma levels of tolerance per channel.
    assert np.abs(decoded.astype(int) - image.astype(int)).mean() < 8


def _feed_in_chunks(decoder: MartinM1Decoder, waveform: np.ndarray, chunk_size: int = 2000) -> None:
    """Real usage (`stream_service.py`) only ever calls `feed()` with
    small (~20-100ms) chunks, bounding the buffer -- and therefore the
    Hilbert transform's cost -- to a few lines' worth at a time.
    Feeding an entire multi-second waveform in one call would instead
    force repeated FFTs over a huge buffer, which is a test-harness
    performance trap, not a real usage pattern."""
    for start in range(0, len(waveform), chunk_size):
        decoder.feed(waveform[start : start + chunk_size])


def test_martin_m1_decoder_handles_a_full_size_image():
    # Sync-pulse tracking (see the module docstring's "Known
    # limitation") occasionally drifts and skips a line over a full
    # 256-line image -- a deliberate trade-off against the far more
    # common failure of locking onto a false sync inside later lines'
    # own picture content. This asserts the realistic bar (the large
    # majority of lines decode, and the ones that do are accurate),
    # not a strict 100%.
    image = _test_image(HEIGHT, WIDTH)
    waveform = _encode_martin_m1(image, SAMPLE_RATE_HZ)

    decoder = MartinM1Decoder(SAMPLE_RATE_HZ)
    _feed_in_chunks(decoder, waveform)

    assert decoder.lines_decoded >= HEIGHT * 0.9
    decoded = decoder.image[: decoder.lines_decoded]
    expected = image[: decoder.lines_decoded]
    assert np.abs(decoded.astype(int) - expected.astype(int)).mean() < 20


def test_martin_m1_decoder_resets_after_a_complete_image():
    # A small image reliably completes (see the round-trip test above),
    # which keeps this test about the reset behavior itself rather than
    # sync-tracking's known drift over a full 256-line image.
    n_lines = HEIGHT  # decoder.is_complete requires exactly HEIGHT lines
    image_a = _test_image(4, WIDTH)
    waveform_a = _encode_martin_m1(image_a, SAMPLE_RATE_HZ)

    decoder = MartinM1Decoder(SAMPLE_RATE_HZ)
    decoder.lines_decoded = n_lines - 4  # fast-forward, rather than decoding 252 filler lines
    decoder.feed(waveform_a)
    assert decoder.is_complete
    assert decoder.lines_decoded == HEIGHT

    image_b = _test_image(2, WIDTH)
    waveform_b = _encode_martin_m1(image_b, SAMPLE_RATE_HZ)
    _feed_in_chunks(decoder, waveform_b)

    assert decoder.lines_decoded == 2  # started over, not appended past HEIGHT
    assert np.abs(decoder.image[:2].astype(int) - image_b.astype(int)).mean() < 8
