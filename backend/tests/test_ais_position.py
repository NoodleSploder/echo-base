"""AIS Class A position report decoding: a synthetic payload with known
lat/lon fields round-trips back through `parse_class_a_position`,
matching the "build known bits, verify decode" pattern `test_mode_s.py`
uses for ADS-B type codes (no widely-published reference test vector
for this one, unlike ADS-B's CPR example, so this leans on the
ITU-R M.1371 bit layout being implemented correctly rather than an
external reference).
"""
from __future__ import annotations

import pytest

from app.services.decoders.ais_position import parse_class_a_position

_MESSAGE_BITS = 168


def _bits_from_int(value: int, n_bits: int) -> list[int]:
    if value < 0:
        value += 1 << n_bits  # two's complement
    return [(value >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]


def _build_position_report(
    message_type: int, mmsi: int, latitude: float, longitude: float
) -> list[int]:
    lon_raw = round(longitude * 600_000)
    lat_raw = round(latitude * 600_000)
    bits = (
        _bits_from_int(message_type, 6)
        + _bits_from_int(0, 2)  # repeat indicator
        + _bits_from_int(mmsi, 30)
        + _bits_from_int(0, 4)  # nav status
        + _bits_from_int(0, 8)  # rate of turn
        + _bits_from_int(0, 10)  # speed over ground
        + _bits_from_int(0, 1)  # position accuracy
        + _bits_from_int(lon_raw, 28)
        + _bits_from_int(lat_raw, 27)
    )
    return bits + [0] * (_MESSAGE_BITS - len(bits))


def test_parse_class_a_position_round_trips_known_coordinates():
    bits = _build_position_report(1, 366123456, latitude=37.8199, longitude=-122.4783)
    position = parse_class_a_position(bits)
    assert position is not None
    assert position.latitude == pytest.approx(37.8199, abs=1e-4)
    assert position.longitude == pytest.approx(-122.4783, abs=1e-4)


def test_parse_class_a_position_handles_negative_coordinates_near_prime_meridian():
    bits = _build_position_report(3, 100000000, latitude=-33.8568, longitude=151.2153)
    position = parse_class_a_position(bits)
    assert position is not None
    assert position.latitude == pytest.approx(-33.8568, abs=1e-4)
    assert position.longitude == pytest.approx(151.2153, abs=1e-4)


def test_parse_class_a_position_returns_none_for_non_position_message_type():
    bits = _build_position_report(5, 366123456, latitude=37.8199, longitude=-122.4783)
    assert parse_class_a_position(bits) is None


def test_parse_class_a_position_returns_none_when_not_available():
    # Longitude/latitude sentinels meaning "position not available".
    bits = (
        _bits_from_int(1, 6)
        + _bits_from_int(0, 2)
        + _bits_from_int(366123456, 30)
        + _bits_from_int(0, 4)
        + _bits_from_int(0, 8)
        + _bits_from_int(0, 10)
        + _bits_from_int(0, 1)
        + _bits_from_int(181 * 600_000, 28)
        + _bits_from_int(91 * 600_000, 27)
    )
    bits += [0] * (_MESSAGE_BITS - len(bits))
    assert parse_class_a_position(bits) is None


def test_parse_class_a_position_returns_none_for_short_payload():
    assert parse_class_a_position(_bits_from_int(1, 6) + _bits_from_int(0, 2)) is None
