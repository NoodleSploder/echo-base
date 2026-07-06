"""ADS-B CPR position decoding: verified against the widely-used
reference even/odd message pair (Junzi Sun's pyModeS test suite;
also appears in ICAO/RTCA CPR decode worked examples), a real
even+odd hex message pair whose correct decoded position
(52.2572, 3.91937 -- central Netherlands) is independently documented,
not something this test invented.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.decoders.adsb_position import (
    AirbornePositionFrame,
    CprPositionResolver,
    decode_global_position,
    parse_airborne_position,
)

# 8D40621D58C382D690C8AC2863A7 (even) / 8D40621D58C386435CC412692AD6 (odd)
EVEN_FRAME = AirbornePositionFrame(odd=False, lat_cpr=93000, lon_cpr=51372)
ODD_FRAME = AirbornePositionFrame(odd=True, lat_cpr=74158, lon_cpr=50194)


def _hex_to_me_bits(hex_message: str) -> list[int]:
    n_bits = len(hex_message) * 4
    value = int(hex_message, 16)
    bits = [(value >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]
    return bits[32:88]


def test_parse_airborne_position_extracts_reference_frames():
    even = parse_airborne_position(_hex_to_me_bits("8D40621D58C382D690C8AC2863A7"))
    odd = parse_airborne_position(_hex_to_me_bits("8D40621D58C386435CC412692AD6"))
    assert even == EVEN_FRAME
    assert odd == ODD_FRAME


def test_parse_airborne_position_ignores_non_position_type_codes():
    # A type-code-1 (aircraft identification) ME field shouldn't parse as a position.
    me_bits = [0, 0, 0, 0, 1] + [0] * 51
    assert parse_airborne_position(me_bits) is None


def test_decode_global_position_matches_reference_even_anchored():
    result = decode_global_position(EVEN_FRAME, ODD_FRAME, use_odd=False)
    assert result is not None
    lat, lon = result
    assert lat == pytest.approx(52.2572, abs=1e-3)
    assert lon == pytest.approx(3.91937, abs=1e-3)


def test_decode_global_position_returns_none_on_nl_mismatch():
    # A pair near a longitude-zone-count boundary (~86.5deg lat, where
    # NL flips from 3 to 2) resolves to two implied latitudes just far
    # enough apart that their NL values disagree -- found by brute-force
    # search, not hand-picked, since arbitrary "far apart" values
    # usually still land in the same NL zone and wouldn't exercise this
    # rejection path at all.
    near_pole_even = AirbornePositionFrame(odd=False, lat_cpr=55038, lon_cpr=0)
    near_pole_odd = AirbornePositionFrame(odd=True, lat_cpr=24604, lon_cpr=0)
    assert decode_global_position(near_pole_even, near_pole_odd, use_odd=True) is None


def test_cpr_position_resolver_pairs_even_and_odd():
    resolver = CprPositionResolver()
    t0 = datetime(2026, 1, 1, tzinfo=UTC)

    assert resolver.update("4840D6", EVEN_FRAME, t0) is None  # only one half so far
    result = resolver.update("4840D6", ODD_FRAME, t0 + timedelta(seconds=0.5))
    assert result is not None
    lat, lon = result
    # The resolver anchors to whichever frame arrived *last* (the odd
    # one here) -- a legitimately slightly different value than the
    # even-anchored reference above, since a real aircraft moves in the
    # ~0.5s between an even and odd report.
    assert lat == pytest.approx(52.2658, abs=1e-3)
    assert lon == pytest.approx(3.9389, abs=1e-3)


def test_cpr_position_resolver_rejects_stale_pairs():
    resolver = CprPositionResolver()
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    resolver.update("4840D6", EVEN_FRAME, t0)
    stale_result = resolver.update("4840D6", ODD_FRAME, t0 + timedelta(seconds=30))
    assert stale_result is None


def test_cpr_position_resolver_keeps_aircraft_independent():
    resolver = CprPositionResolver()
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    resolver.update("AAAAAA", EVEN_FRAME, t0)
    # A different aircraft's odd frame shouldn't pair with AAAAAA's even frame.
    assert resolver.update("BBBBBB", ODD_FRAME, t0) is None


