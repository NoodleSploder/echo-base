"""AIS decoder: a synthetic HDLC/NRZI frame (message type + MMSI,
CRC-16 computed and bit-stuffed like a real AIS transmission) built as
a bipolar "discriminator output" signal round-trips back through
bit-sync + NRZI decode + de-stuffing + FCS validation to the exact
message_type/mmsi it was built from.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.services.decoders.ais import AisDecoder
from app.services.decoders.ax25 import compute_fcs

SAMPLE_RATE_HZ = 48_000  # same decimated audio rate APRS/SAME already use


def _bits_from_int(value: int, n_bits: int) -> list[int]:
    return [(value >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]


def _pack_bytes_lsb_first(bits: list[int]) -> bytes:
    out = bytearray()
    for start in range(0, len(bits), 8):
        value = 0
        for i, bit in enumerate(bits[start : start + 8]):
            value |= bit << i
        out.append(value)
    return bytes(out)


def _bit_stuff(bits: list[int]) -> list[int]:
    out: list[int] = []
    ones_run = 0
    for bit in bits:
        out.append(bit)
        if bit == 1:
            ones_run += 1
            if ones_run == 5:
                out.append(0)
                ones_run = 0
        else:
            ones_run = 0
    return out


def _byte_to_wire_bits(value: int) -> list[int]:
    """Inverse of `_pack_bytes_lsb_first`: the raw bit sequence that
    packs back into `value` under that same LSB-first-per-byte
    convention (bits[0] of each 8-bit group is the LSB)."""
    return [(value >> i) & 1 for i in range(8)]


def _build_ais_frame(message_type: int, mmsi: int) -> list[int]:
    # AIS payload fields (message type, MMSI, ...) are MSB-first
    # directly in the raw wire bit sequence per ITU-R M.1371 -- unlike
    # the FCS, there's no separate "byte" repacking step for these.
    payload_bits = _bits_from_int(message_type, 6) + [0, 0] + _bits_from_int(mmsi, 30) + [0] * 10
    assert len(payload_bits) % 8 == 0
    packed = _pack_bytes_lsb_first(payload_bits)
    fcs = compute_fcs(packed)
    fcs_bits = _byte_to_wire_bits(fcs & 0xFF) + _byte_to_wire_bits((fcs >> 8) & 0xFF)
    return payload_bits + fcs_bits


def _nrzi_encode(bits: list[int]) -> list[int]:
    level = 1
    out = []
    for bit in bits:
        if bit == 0:
            level ^= 1
        out.append(level)
    return out


def _synthesize_signal(frame_bits: list[int], samples_per_bit: int) -> np.ndarray:
    flag = [0, 1, 1, 1, 1, 1, 1, 0]
    stuffed = _bit_stuff(frame_bits)
    full_bits = flag + stuffed + flag
    nrzi_bits = _nrzi_encode(full_bits)
    samples: list[float] = []
    for bit in nrzi_bits:
        samples.extend([1.0 if bit else -1.0] * samples_per_bit)
    return np.array(samples, dtype=np.float32)


@pytest.mark.parametrize(("message_type", "mmsi"), [(1, 123456789), (5, 987654321), (18, 111222333)])
def test_synthetic_ais_frame_round_trips(message_type, mmsi):
    frame_bits = _build_ais_frame(message_type, mmsi)
    samples_per_bit = round(SAMPLE_RATE_HZ / 9600)
    signal = _synthesize_signal(frame_bits, samples_per_bit)
    # Random (not constant) padding -- a constant DC level before/after
    # the frame can accidentally coincide with the leading flag's own
    # NRZI level for several bits (a real receiver's noise floor
    # wouldn't do this), masking it. Real "silence" is noisy, not a
    # clean symbol level.
    rng = np.random.default_rng(3)
    pre = rng.choice([-1.0, 1.0], size=50).astype(np.float32)
    post = rng.choice([-1.0, 1.0], size=50).astype(np.float32)
    padded = np.concatenate([pre, signal, post])

    decoder = AisDecoder(SAMPLE_RATE_HZ)
    messages = decoder.feed(padded)

    assert len(messages) == 1
    assert messages[0]["message_type"] == message_type
    assert messages[0]["mmsi"] == mmsi


def test_decoder_ignores_noise():
    rng = np.random.default_rng(7)
    noise = rng.uniform(-1, 1, 5000).astype(np.float32)
    decoder = AisDecoder(SAMPLE_RATE_HZ)
    assert decoder.feed(noise) == []


def test_decoder_dedupes_repeated_message():
    frame_bits = _build_ais_frame(1, 123456789)
    samples_per_bit = round(SAMPLE_RATE_HZ / 9600)
    signal = _synthesize_signal(frame_bits, samples_per_bit)
    rng = np.random.default_rng(9)
    pre = rng.choice([-1.0, 1.0], size=50).astype(np.float32)
    post = rng.choice([-1.0, 1.0], size=50).astype(np.float32)
    padded = np.concatenate([pre, signal, post])

    decoder = AisDecoder(SAMPLE_RATE_HZ)
    first = decoder.feed(padded)
    second = decoder.feed(padded)
    assert len(first) == 1
    assert second == []
