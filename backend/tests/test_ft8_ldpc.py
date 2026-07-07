"""FT8 (174,91) LDPC belief-propagation decoder: cross-verified
against ft8_lib's real `ldpc.c` `bp_decode`, compiled and run directly
-- both test vectors below (the exact codeword bits and, for the noisy
case, the exact per-bit LLRs) are what that compiled reference
produced. See the diary entry: the LLR sign convention this module
uses is the *opposite* of `ldpc.c`'s own source comment, verified
empirically rather than trusted from the comment (the documented
convention decoded with 156/174 bits wrong; the opposite decoded
perfectly).
"""
from __future__ import annotations

from app.services.decoders.ft8_ldpc import bp_decode

_CODEWORD_HEX = "aaaaaaaaaaaaaaaaaaaa5e4f4c3b3fb0f02dcdaa2d14"


def _hex_to_bits(hex_str: str, n_bits: int) -> list[int]:
    value = int(hex_str, 16)
    total_bits = len(hex_str) * 4
    return [(value >> (total_bits - 1 - i)) & 1 for i in range(n_bits)]


def test_bp_decode_perfect_confidence_recovers_exact_codeword():
    bits = _hex_to_bits(_CODEWORD_HEX, 174)
    llr = [4.6 if b else -4.6 for b in bits]
    decoded, errors = bp_decode(llr, max_iters=30)
    assert errors == 0
    assert decoded == bits


def test_bp_decode_recovers_from_flipped_bits_with_moderate_confidence():
    bits_str = (
        "101010101010101010101010101010101010101010101010101010101010101010101010101010100"
        "101111001001111010011000011101100111111101100001111000000101101110011011010101000"
        "101101000101"
    )
    bits = [int(c) for c in bits_str]
    assert len(bits) == 174

    llr_str = (
        "2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 -2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 "
        "-2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 2.0 2.0 2.0 2.0 "
        "-2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 "
        "-2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 2.0 -2.0 -2.0 -2.0 2.0 -2.0 2.0 "
        "-2.0 2.0 -2.0 -2.0 2.0 2.0 2.0 2.0 2.0 2.0 2.0 -2.0 2.0 -2.0 -2.0 2.0 2.0 2.0 2.0 2.0 "
        "2.0 -2.0 -2.0 2.0 2.0 -2.0 -2.0 -2.0 -2.0 2.0 2.0 2.0 -2.0 2.0 2.0 -2.0 -2.0 2.0 2.0 "
        "2.0 2.0 2.0 2.0 2.0 -2.0 2.0 2.0 -2.0 -2.0 -2.0 -2.0 2.0 2.0 2.0 2.0 -2.0 -2.0 -2.0 "
        "-2.0 -2.0 -2.0 2.0 -2.0 2.0 2.0 -2.0 2.0 2.0 2.0 -2.0 -2.0 2.0 2.0 -2.0 2.0 2.0 -2.0 "
        "2.0 -2.0 2.0 -2.0 2.0 -2.0 -2.0 -2.0 2.0 -2.0 2.0 2.0 -2.0 2.0 -2.0 -2.0 -2.0 2.0 -2.0 "
        "2.0"
    )
    llr = [float(x) for x in llr_str.split()]
    assert len(llr) == 174

    decoded, errors = bp_decode(llr, max_iters=30)
    assert errors == 0
    assert decoded == bits  # recovered the original 8-bit-flipped codeword exactly
