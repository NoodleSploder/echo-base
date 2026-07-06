"""ADS-B airborne position decoding (CPR -- Compact Position Reporting).

The natural follow-up `mode_s.py` deliberately deferred: DF17/18
extended squitters with type code 9-18 (barometric-altitude airborne
position) or 20-22 (GNSS-altitude airborne position) encode latitude/
longitude as two 17-bit fractions of a 360deg/awkward-numbered-zone
grid, alternating between an "even" and "odd" encoding every ~0.5s.
Neither frame alone is enough to recover a real lat/lon -- you need one
of each (the "global CPR" algorithm below), which is why this is a
*pairing* problem (`CprPositionResolver`, stateful, one per receiver)
layered on top of `parse_airborne_position` (stateless, one frame at a
time).

Algorithm and constants are the standard ICAO Annex 10 / RTCA DO-260B
CPR decode -- verified against the widely-used reference test vectors
(an even/odd message pair from Junzi Sun's pyModeS test suite,
known-correct result: 52.2572, 3.91937 -- central Netherlands) in
`test_adsb_position.py`, not just "the math didn't crash."
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

NZ = 15  # number of latitude zones between the equator and a pole
_LAT_ZONE_SIZE_EVEN = 360.0 / (4 * NZ)
_LAT_ZONE_SIZE_ODD = 360.0 / (4 * NZ - 1)
_CPR_SCALE = 131072.0  # 2^17 -- CPR lat/lon fields are 17-bit fractions

AIRBORNE_POSITION_BARO_TYPE_CODES = frozenset(range(9, 19))  # TC 9-18
AIRBORNE_POSITION_GNSS_TYPE_CODES = frozenset(range(20, 23))  # TC 20-22
AIRBORNE_POSITION_TYPE_CODES = AIRBORNE_POSITION_BARO_TYPE_CODES | AIRBORNE_POSITION_GNSS_TYPE_CODES

# Standard "don't pair frames that are too far apart in time" threshold
# (an aircraft can move enough between distant even/odd reports that
# pairing them would silently produce a wrong position rather than an
# obviously-invalid one) -- 10s is the conventional dump1090-family
# value, generous for ADS-B's typical ~0.5s squitter rate.
MAX_PAIR_AGE_SECONDS = 10.0


@dataclass(frozen=True)
class AirbornePositionFrame:
    odd: bool  # the CPR format flag: False = even frame, True = odd frame
    lat_cpr: int  # 0..131071 (17-bit)
    lon_cpr: int  # 0..131071 (17-bit)


def parse_airborne_position(me_bits: list[int]) -> AirbornePositionFrame | None:
    """`me_bits` is the 56-bit ME field (bits 33-88 of the full Mode S
    frame -- i.e. `frame_bits[32:88]`). Returns None if the type code
    isn't an airborne position message."""
    if len(me_bits) != 56:
        return None
    type_code = int("".join(map(str, me_bits[0:5])), 2)
    if type_code not in AIRBORNE_POSITION_TYPE_CODES:
        return None
    odd = bool(me_bits[21])
    lat_cpr = int("".join(map(str, me_bits[22:39])), 2)
    lon_cpr = int("".join(map(str, me_bits[39:56])), 2)
    return AirbornePositionFrame(odd=odd, lat_cpr=lat_cpr, lon_cpr=lon_cpr)


def _cpr_nl(lat: float) -> int:
    """Number of longitude zones at a given latitude -- 59 at the
    equator, shrinking to 1 near the poles (a degree of longitude
    covers much less ground near a pole than at the equator)."""
    if lat == 0:
        return 59
    if abs(lat) >= 87:
        return 1
    a = 1 - math.cos(math.pi / (2 * NZ))
    b = math.cos(math.radians(abs(lat))) ** 2
    return math.floor(2 * math.pi / math.acos(1 - a / b))


def decode_global_position(
    even: AirbornePositionFrame, odd: AirbornePositionFrame, *, use_odd: bool
) -> tuple[float, float] | None:
    """Resolves one even+odd CPR frame pair to a real (lat, lon).
    `use_odd` picks which of the two frames' *longitude* zone count and
    reported time the result is anchored to -- pass whichever frame
    arrived more recently, the standard "most recent report wins"
    convention. Returns None if the pair is inconsistent (the even and
    odd frames don't agree on how many longitude zones exist at this
    latitude -- can happen if the two frames are from different
    aircraft/times and shouldn't have been paired at all)."""
    lat_e = even.lat_cpr / _CPR_SCALE
    lat_o = odd.lat_cpr / _CPR_SCALE

    j = math.floor(59 * lat_e - 60 * lat_o + 0.5)
    lat_even = _LAT_ZONE_SIZE_EVEN * ((j % 60) + lat_e)
    lat_odd = _LAT_ZONE_SIZE_ODD * ((j % 59) + lat_o)
    if lat_even >= 270:
        lat_even -= 360
    if lat_odd >= 270:
        lat_odd -= 360

    nl_even = _cpr_nl(lat_even)
    nl_odd = _cpr_nl(lat_odd)
    if nl_even != nl_odd:
        return None

    lon_e = even.lon_cpr / _CPR_SCALE
    lon_o = odd.lon_cpr / _CPR_SCALE

    if use_odd:
        ni = max(nl_odd - 1, 1)
        m = math.floor(lon_e * (nl_odd - 1) - lon_o * nl_odd + 0.5)
        lon = (360.0 / ni) * ((m % ni) + lon_o)
        lat = lat_odd
    else:
        ni = max(nl_even, 1)
        m = math.floor(lon_e * (nl_even - 1) - lon_o * nl_even + 0.5)
        lon = (360.0 / ni) * ((m % ni) + lon_e)
        lat = lat_even

    if lon > 180:
        lon -= 360
    return lat, lon


class CprPositionResolver:
    """Tracks the most recent even/odd `AirbornePositionFrame` per
    ICAO address and resolves a real position as soon as both halves
    of a pair are available and recent enough. One instance is shared
    across a whole capture session (see `ModeSDecoder`), not
    per-aircraft -- aircraft come and go, so this is keyed by ICAO
    address internally rather than needing external per-aircraft
    bookkeeping."""

    def __init__(self) -> None:
        self._frames: dict[str, dict[bool, tuple[AirbornePositionFrame, datetime]]] = {}

    def update(
        self, icao: str, frame: AirbornePositionFrame, timestamp: datetime
    ) -> tuple[float, float] | None:
        entry = self._frames.setdefault(icao, {})
        entry[frame.odd] = (frame, timestamp)

        other = entry.get(not frame.odd)
        if other is None:
            return None
        other_frame, other_timestamp = other
        if abs((timestamp - other_timestamp).total_seconds()) > MAX_PAIR_AGE_SECONDS:
            return None

        even_frame, odd_frame = (other_frame, frame) if frame.odd else (frame, other_frame)
        return decode_global_position(even_frame, odd_frame, use_odd=frame.odd)
