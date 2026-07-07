"""FT8 CRC-14: cross-verified bit-for-bit against ft8_lib's real
`crc.c`, compiled and run directly (not just re-derived from the spec)
-- see the diary entry for how. These two test vectors are exactly
what that compiled reference produced for a fixed pseudo-random 77-bit
payload and an all-zero payload.
"""
from __future__ import annotations

from app.services.decoders.ft8_crc import add_crc, verify_crc


def _crc_value(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def test_add_crc_matches_compiled_reference_pseudo_random_payload():
    payload = [(i * 7 + 3) % 2 for i in range(77)]
    result = add_crc(payload)
    assert len(result) == 91
    assert _crc_value(result[77:91]) == 4850  # from the real compiled ftx_add_crc


def test_add_crc_matches_compiled_reference_zero_payload():
    payload = [0] * 77
    result = add_crc(payload)
    assert _crc_value(result[77:91]) == 0  # from the real compiled ftx_add_crc


def test_verify_crc_accepts_a_correctly_added_crc():
    payload = [(i * 11 + 1) % 2 for i in range(77)]
    with_crc = add_crc(payload)
    assert verify_crc(with_crc) is True


def test_verify_crc_rejects_a_corrupted_payload():
    payload = [(i * 11 + 1) % 2 for i in range(77)]
    with_crc = add_crc(payload)
    corrupted = with_crc.copy()
    corrupted[10] ^= 1
    assert verify_crc(corrupted) is False
