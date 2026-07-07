"""FT8's CRC-14, computed over the 77-bit payload zero-extended to 82
bits (per the FT8 spec -- 'the CRC is calculated on the source-encoded
message, zero-extended from 77 to 82 bits'), producing a 91-bit
payload+CRC input to the LDPC encoder. Same polynomial/bit-order as
ft8_lib's `crc.c`.
"""
from __future__ import annotations

from app.services.decoders.ft8_constants import CRC_POLYNOMIAL, CRC_WIDTH

_TOP_BIT = 1 << (CRC_WIDTH - 1)
_MASK = (1 << CRC_WIDTH) - 1


def compute_crc14(bits: list[int]) -> int:
    """`bits` is a 0/1 list, MSB-first bit-by-bit modulo-2 division --
    matches ft8_lib's `ftx_compute_crc` bit-for-bit rather than a
    byte-table variant, since the input here is naturally a bit list
    (from `pack_standard_message`/an LDPC-decoded codeword), not bytes."""
    remainder = 0
    for bit in bits:
        # XOR the incoming bit into the top position, matching a
        # byte-at-a-time CRC's "bring the next byte in" step but one
        # bit at a time.
        remainder ^= bit << (CRC_WIDTH - 1)
        if remainder & _TOP_BIT:
            remainder = ((remainder << 1) ^ CRC_POLYNOMIAL) & _MASK
        else:
            remainder = (remainder << 1) & _MASK
    return remainder & _MASK


def add_crc(payload_bits: list[int]) -> list[int]:
    """`payload_bits` is 77 bits -> returns 91 bits (77 payload + 14 CRC),
    the LDPC encoder's `k=91` input. The CRC is computed over the
    payload zero-extended to 82 bits, per spec."""
    assert len(payload_bits) == 77
    extended = payload_bits + [0] * 5
    checksum = compute_crc14(extended)
    checksum_bits = [(checksum >> (CRC_WIDTH - 1 - i)) & 1 for i in range(CRC_WIDTH)]
    return payload_bits + checksum_bits


def verify_crc(payload_with_crc_bits: list[int]) -> bool:
    """`payload_with_crc_bits` is 91 bits (77 payload + 14 CRC) -- True
    if the trailing CRC matches the payload's own recomputed checksum."""
    assert len(payload_with_crc_bits) == 91
    payload = payload_with_crc_bits[:77]
    received_crc_bits = payload_with_crc_bits[77:91]
    received_crc = 0
    for bit in received_crc_bits:
        received_crc = (received_crc << 1) | bit
    extended = payload + [0] * 5
    return compute_crc14(extended) == received_crc
