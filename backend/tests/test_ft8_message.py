"""FT8 standard message unpacking: cross-verified against ft8_lib's
real `message.c` (`ftx_message_encode_std`), compiled and run directly
-- every payload hex string below is exactly what that compiled
reference produced for the given callsigns/grid/report, not something
this project invented.
"""
from __future__ import annotations

from app.services.decoders.ft8_message import (
    Ft8StandardMessage,
    grid_to_lat_lon,
    unpack_standard_message,
)


def _hex_to_77bits(hex_str: str) -> list[int]:
    raw = bytes.fromhex(hex_str.replace(" ", ""))
    bits = []
    for byte in raw:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits[:77]


def test_unpack_cq_with_grid():
    bits = _hex_to_77bits("00 00 00 20 4d ef 1a 8a 19 88")
    assert unpack_standard_message(bits) == Ft8StandardMessage("CQ", "K1ABC", "FN42")


def test_unpack_reply_with_signal_report():
    bits = _hex_to_77bits("0c 29 3b 80 4d ef 1a 9f a9 c8")
    assert unpack_standard_message(bits) == Ft8StandardMessage("W9XYZ", "K1ABC", "-12")


def test_unpack_cq_with_slash_p_suffix():
    bits = _hex_to_77bits("00 00 00 20 5f f5 68 ca 16 d0")
    assert unpack_standard_message(bits) == Ft8StandardMessage("CQ", "W1AW/P", "FN31")


def test_unpack_cq_with_numeric_modifier():
    bits = _hex_to_77bits("00 00 07 e0 4e 88 e0 88 37 08")
    assert unpack_standard_message(bits) == Ft8StandardMessage("CQ 123", "K5ABC", "EM12")


def test_unpack_negative_signal_report_with_r_prefix():
    bits = _hex_to_77bits("e2 01 af 70 5f f5 68 bf ab 88")
    assert unpack_standard_message(bits) == Ft8StandardMessage("VK2DEF", "W1AW", "R-05")


def test_unpack_returns_none_for_a_hashed_callsign():
    # "N0CALL" doesn't fit the base-37 standard-callsign encoding (4
    # trailing letters exceeds the scheme's 3-letter suffix limit), so
    # the real encoder itself falls back to a 22-bit callsign hash --
    # unsupported here (no hash table), so this must return None
    # rather than a wrong guess.
    bits = _hex_to_77bits("00 61 5f 90 1e 52 92 1f a4 c8")
    assert unpack_standard_message(bits) is None


def test_grid_to_lat_lon_fn42_is_new_england():
    result = grid_to_lat_lon("FN42")
    assert result is not None
    lat, lon = result
    assert 40 < lat < 45
    assert -75 < lon < -68


def test_grid_to_lat_lon_rejects_non_grid_text():
    assert grid_to_lat_lon("RRR") is None
    assert grid_to_lat_lon("-12") is None
    assert grid_to_lat_lon("73") is None
