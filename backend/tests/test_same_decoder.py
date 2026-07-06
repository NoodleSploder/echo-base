"""Round-trip test for the SAME (NOAA Weather Radio) decoder: synthesizes
a known alert header as a real SAME-format FSK audio waveform and
checks the decoder recovers it exactly. Same rationale as
test_afsk_decoder.py -- real over-the-air reception can't be relied on
in this environment, so a synthetic encode/decode round trip is the
actual correctness proof.
"""
from __future__ import annotations

import numpy as np

from app.services.decoders.same import MARK_HZ, PREAMBLE_BYTE, SPACE_HZ, SameDecoder

SAMPLE_RATE_HZ = 48_000
BAUD = 520.83


def _byte_to_bits_lsb_first(byte: int) -> list[int]:
    return [(byte >> i) & 1 for i in range(8)]


def _synthesize_same(header: str) -> np.ndarray:
    bits: list[int] = []
    for _ in range(16):
        bits.extend(_byte_to_bits_lsb_first(PREAMBLE_BYTE))
    for char in header:
        bits.extend(_byte_to_bits_lsb_first(ord(char)))
    # Trailing silence-ish filler so the decoder's printable-run match
    # terminates right after the header, like real dead air/next-repeat
    # preamble would.
    bits.extend([0] * 64)

    # Real audio is continuous; a bit's duration in samples isn't an
    # integer (48000/520.83 != a whole number), so truncating each bit to
    # round(samples_per_bit) samples would discard a fractional remainder
    # every single bit and drift by a full bit period over a ~700-bit
    # message. Track a running cursor instead, like the decoder itself
    # does, so cumulative bit-boundary timing stays exact.
    samples_per_bit = SAMPLE_RATE_HZ / BAUD
    segments = []
    phase = 0.0
    cursor = 0.0
    for bit in bits:
        freq = MARK_HZ if bit == 1 else SPACE_HZ
        next_cursor = cursor + samples_per_bit
        n = int(round(next_cursor)) - int(round(cursor))
        cursor = next_cursor
        t = np.arange(n)
        segments.append(np.sin(2 * np.pi * freq * t / SAMPLE_RATE_HZ + phase))
        phase = (phase + 2 * np.pi * freq * n / SAMPLE_RATE_HZ) % (2 * np.pi)
    return np.concatenate(segments).astype(np.float32)


def test_same_round_trip_recovers_known_header():
    header = "ZCZC-WXR-RWT-020103-020209-020091-020209+0030-1231423-KLOX/NWS-"
    audio = _synthesize_same(header)

    decoder = SameDecoder(SAMPLE_RATE_HZ)
    headers = decoder.feed(audio)

    assert header in headers


def test_same_decoder_ignores_silence():
    decoder = SameDecoder(SAMPLE_RATE_HZ)
    silence = np.zeros(SAMPLE_RATE_HZ, dtype=np.float32)
    assert decoder.feed(silence) == []
