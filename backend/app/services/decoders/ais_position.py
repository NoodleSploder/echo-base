"""AIS position report field decoding (ITU-R M.1371).

Unlike ADS-B's CPR encoding, an AIS position report needs no frame-
pairing across time -- longitude/latitude are each a single signed
fixed-point field within one message, so this is a stateless "parse
this message's bits" module, not a stateful tracker the way
`adsb_position.py`'s `CprPositionResolver` is.

Scope: **Class A position reports (message types 1, 2, 3)** only --
the most common vessel-tracking messages. Class B (types 18/19,
smaller craft/AIS transponders) uses a similar but distinctly
different bit layout and is a natural follow-up, same "achievable
subset first" reasoning as every other decoder gap in this project.
"""
from __future__ import annotations

from dataclasses import dataclass

CLASS_A_POSITION_REPORT_TYPES = frozenset({1, 2, 3})
# Longitude/latitude are 28/27-bit two's-complement fields, in units of
# 1/10000 minute (i.e. degrees * 600000) -- ITU-R M.1371's own scaling.
_COORDINATE_SCALE = 600_000.0
_LONGITUDE_BITS = 28
_LATITUDE_BITS = 27
# The sentinel values meaning "position not available", in raw units.
_LONGITUDE_NOT_AVAILABLE = 181 * 600_000
_LATITUDE_NOT_AVAILABLE = 91 * 600_000
_MIN_PAYLOAD_BITS_FOR_POSITION = 89 + _LATITUDE_BITS  # through the end of the latitude field


@dataclass(frozen=True)
class AisPosition:
    latitude: float
    longitude: float


def _twos_complement(value: int, n_bits: int) -> int:
    if value >= 1 << (n_bits - 1):
        value -= 1 << n_bits
    return value


def parse_class_a_position(payload_bits: list[int]) -> AisPosition | None:
    """`payload_bits` is the destuffed AIS payload (as `AisDecoder.feed`
    already extracts message_type/mmsi from) -- MSB-first per ITU-R
    M.1371's own bit numbering. Returns None if this isn't a Class A
    position report, the payload is too short to contain one, or the
    position fields are explicitly marked "not available"."""
    if len(payload_bits) < _MIN_PAYLOAD_BITS_FOR_POSITION:
        return None
    message_type = int("".join(map(str, payload_bits[0:6])), 2)
    if message_type not in CLASS_A_POSITION_REPORT_TYPES:
        return None

    longitude_raw = int("".join(map(str, payload_bits[61:89])), 2)
    latitude_raw = int("".join(map(str, payload_bits[89:116])), 2)

    if longitude_raw == _LONGITUDE_NOT_AVAILABLE or latitude_raw == _LATITUDE_NOT_AVAILABLE:
        return None

    longitude = _twos_complement(longitude_raw, _LONGITUDE_BITS) / _COORDINATE_SCALE
    latitude = _twos_complement(latitude_raw, _LATITUDE_BITS) / _COORDINATE_SCALE
    return AisPosition(latitude=latitude, longitude=longitude)
