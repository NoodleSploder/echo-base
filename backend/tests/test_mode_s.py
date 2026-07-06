"""Mode S decoder: a synthetic DF17 frame, CRC-computed and encoded as
a real PPM/preamble IQ waveform, round-trips back through
preamble detection + bit-slicing + CRC validation to the exact
DF/ICAO/type-code it was built from.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.services.decoders.mode_s import ModeSDecoder, crc24_remainder

SAMPLE_RATE_HZ = 2_000_000  # 2 samples/us -- the clean-integer rate ADS-B tooling standardizes on


def _bits_from_int(value: int, n_bits: int) -> list[int]:
    return [(value >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]


def _build_df17_frame(icao: int, type_code: int) -> list[int]:
    df_ca = _bits_from_int((17 << 3) | 0, 8)  # DF=17 (5 bits), CA=0 (3 bits)
    icao_bits = _bits_from_int(icao, 24)
    me_bits = _bits_from_int(type_code, 5) + [0] * 51  # TC + zeroed remainder of the 56-bit ME field
    payload_bits = df_ca + icao_bits + me_bits
    payload_bytes = bytes(
        sum(payload_bits[i * 8 + j] << (7 - j) for j in range(8)) for i in range(len(payload_bits) // 8)
    )
    crc = crc24_remainder(payload_bytes + b"\x00\x00\x00")
    crc_bits = _bits_from_int(crc, 24)
    return payload_bits + crc_bits


def _synthesize_waveform(bits: list[int], samples_per_us: int) -> np.ndarray:
    half_chip = samples_per_us // 2
    preamble_chips = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]  # pulses at chips 0,2,7,9
    samples: list[float] = []
    for chip in preamble_chips:
        samples.extend([float(chip)] * half_chip)
    for bit in bits:
        samples.extend([1.0] * half_chip if bit else [0.0] * half_chip)
        samples.extend([0.0] * half_chip if bit else [1.0] * half_chip)
    return np.array(samples, dtype=np.complex64)  # magnitude of a real value is itself


def test_crc_self_consistent():
    payload = bytes(range(11)) + b"\x00\x00\x00"
    crc = crc24_remainder(payload[:11] + bytes([0, 0, 0]))
    corrected = payload[:11] + crc.to_bytes(3, "big")
    assert crc24_remainder(corrected) == 0


@pytest.mark.parametrize("type_code", [1, 4, 11, 19])
def test_synthetic_df17_frame_round_trips(type_code):
    icao = 0x4840D6
    bits = _build_df17_frame(icao, type_code)
    waveform = _synthesize_waveform(bits, samples_per_us=2)
    # Pad with silence on both sides, like a real capture chunk would have.
    padded = np.concatenate([np.zeros(50, dtype=np.complex64), waveform, np.zeros(50, dtype=np.complex64)])

    decoder = ModeSDecoder(SAMPLE_RATE_HZ)
    messages = decoder.feed(padded)

    assert len(messages) == 1
    assert messages[0]["df"] == 17
    assert messages[0]["icao"] == "4840D6"
    assert messages[0]["type_code"] == type_code


def test_decoder_ignores_noise():
    rng = np.random.default_rng(42)
    noise = (rng.uniform(-1, 1, 4000) + 1j * rng.uniform(-1, 1, 4000)).astype(np.complex64)
    decoder = ModeSDecoder(SAMPLE_RATE_HZ)
    assert decoder.feed(noise) == []


def test_decoder_dedupes_repeated_message():
    bits = _build_df17_frame(0x4840D6, 4)
    waveform = _synthesize_waveform(bits, samples_per_us=2)

    decoder = ModeSDecoder(SAMPLE_RATE_HZ)
    first = decoder.feed(waveform)
    second = decoder.feed(waveform)
    assert len(first) == 1
    assert second == []


def _build_df17_position_frame(icao: int, odd: bool, lat_cpr: int, lon_cpr: int) -> list[int]:
    df_ca = _bits_from_int((17 << 3) | 0, 8)
    icao_bits = _bits_from_int(icao, 24)
    # ME field: TC=11 (airborne position, barometric altitude) + SS(2) +
    # NICsb(1) + ALT(12), all zeroed (not exercised here) + T(1) + F(1,
    # the odd/even flag) + lat_cpr(17) + lon_cpr(17) = 56 bits.
    me_bits = (
        _bits_from_int(11, 5)
        + [0] * 15  # SS + NICsb + ALT
        + [0]  # T
        + [1 if odd else 0]  # F
        + _bits_from_int(lat_cpr, 17)
        + _bits_from_int(lon_cpr, 17)
    )
    payload_bits = df_ca + icao_bits + me_bits
    payload_bytes = bytes(
        sum(payload_bits[i * 8 + j] << (7 - j) for j in range(8)) for i in range(len(payload_bits) // 8)
    )
    crc = crc24_remainder(payload_bytes + b"\x00\x00\x00")
    crc_bits = _bits_from_int(crc, 24)
    return payload_bits + crc_bits


def test_decoder_resolves_position_from_even_odd_pair():
    # Same reference even/odd CPR values as test_adsb_position.py
    # (8D40621D58C382D690C8AC2863A7 / ...386435CC412692AD6), fed
    # through two real synthesized PPM waveforms rather than calling
    # the CPR math directly -- proves the whole pipeline (preamble
    # detection -> bit slicing -> CRC -> ME field extraction -> CPR
    # pairing) actually connects end to end, not just each piece in
    # isolation.
    icao = 0x40621D
    even_bits = _build_df17_position_frame(icao, odd=False, lat_cpr=93000, lon_cpr=51372)
    odd_bits = _build_df17_position_frame(icao, odd=True, lat_cpr=74158, lon_cpr=50194)

    decoder = ModeSDecoder(SAMPLE_RATE_HZ)
    even_result = decoder.feed(_synthesize_waveform(even_bits, samples_per_us=2))
    assert len(even_result) == 1
    assert "latitude" not in even_result[0]  # only one half of the pair so far

    odd_result = decoder.feed(_synthesize_waveform(odd_bits, samples_per_us=2))
    assert len(odd_result) == 1
    assert odd_result[0]["latitude"] == pytest.approx(52.2658, abs=1e-3)
    assert odd_result[0]["longitude"] == pytest.approx(3.9389, abs=1e-3)
