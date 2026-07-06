"""Parses APRS position reports (lat/lon) out of an AX.25 UI frame's info
field -- the payload `ax25.parse_ax25_frame` already extracts.

Two of APRS's position formats are supported (APRS101.pdf ch. 8-9):

- "Uncompressed": `!`/`=`/`/`/`@` followed by an 8-char latitude, a
  symbol table ID, a 9-char longitude, a symbol code, and a free-text
  comment. Human-readable digits, no real decoding logic beyond string
  slicing.
- "Compressed": the symbol table ID followed directly by two base-91
  values (4 characters each) for latitude/longitude and a symbol code.
  Unlike Mic-E (deliberately *not* implemented here -- see below),
  this is a closed-form mathematical formula, not a lookup table, so
  it can be verified by round-tripping the same formula rather than
  trusting a transcribed reference table.

Mic-E (position encoded in the *destination callsign* via a
substitution table, ch. 10) is common on real trackers but is not
implemented: correctly transcribing its character-class table from
memory, with no real Mic-E traffic available in this environment to
check against, risks a plausible-looking but subtly wrong decoder --
worse than clearly not supporting it. A future implementation should
be checked against real captured Mic-E packets, not just self-consistency.
"""
from __future__ import annotations

from dataclasses import dataclass

_POSITION_DATA_TYPES = "!=/@"
_BASE91_LAT_DIVISOR = 380926  # 91^4 / 180, per APRS101.pdf ch. 9
_BASE91_LON_DIVISOR = 190463  # 91^4 / 360


@dataclass
class AprsPosition:
    latitude: float
    longitude: float
    symbol_table: str
    symbol_code: str
    comment: str


def _parse_latitude(text: str) -> float | None:
    if len(text) != 8:
        return None
    hemisphere = text[7]
    if hemisphere not in "NS":
        return None
    try:
        degrees = int(text[0:2])
        minutes = float(text[2:7])
    except ValueError:
        return None
    value = degrees + minutes / 60
    return -value if hemisphere == "S" else value


def _parse_longitude(text: str) -> float | None:
    if len(text) != 9:
        return None
    hemisphere = text[8]
    if hemisphere not in "EW":
        return None
    try:
        degrees = int(text[0:3])
        minutes = float(text[3:8])
    except ValueError:
        return None
    value = degrees + minutes / 60
    return -value if hemisphere == "W" else value


def _parse_uncompressed(data_type: str, body: str) -> AprsPosition | None:
    if data_type in "/@":
        if len(body) < 7:
            return None
        body = body[7:]  # skip the DHM/HMS timestamp, not needed for position

    if len(body) < 19:
        return None

    latitude = _parse_latitude(body[0:8])
    symbol_table = body[8]
    longitude = _parse_longitude(body[9:18])
    symbol_code = body[18]
    comment = body[19:].strip()

    if latitude is None or longitude is None:
        return None

    return AprsPosition(
        latitude=latitude,
        longitude=longitude,
        symbol_table=symbol_table,
        symbol_code=symbol_code,
        comment=comment,
    )


def _base91_decode(chars: str) -> int | None:
    if len(chars) != 4:
        return None
    value = 0
    for char in chars:
        code = ord(char) - 33
        if not 0 <= code <= 90:
            return None
        value = value * 91 + code
    return value


def _parse_compressed(data_type: str, body: str) -> AprsPosition | None:
    if data_type in "/@":
        if len(body) < 7:
            return None
        body = body[7:]

    if len(body) < 10:
        return None

    symbol_table = body[0]
    lat_value = _base91_decode(body[1:5])
    lon_value = _base91_decode(body[5:9])
    symbol_code = body[9]
    comment = body[10:].strip()

    if lat_value is None or lon_value is None:
        return None

    latitude = 90 - lat_value / _BASE91_LAT_DIVISOR
    longitude = -180 + lon_value / _BASE91_LON_DIVISOR

    return AprsPosition(
        latitude=latitude,
        longitude=longitude,
        symbol_table=symbol_table,
        symbol_code=symbol_code,
        comment=comment,
    )


def parse_aprs_position(info: bytes) -> AprsPosition | None:
    try:
        text = info.decode("ascii")
    except UnicodeDecodeError:
        return None

    if not text or text[0] not in _POSITION_DATA_TYPES:
        return None
    data_type = text[0]
    body = text[1:]

    # A position's first meaningful character disambiguates the two
    # formats: uncompressed latitude always starts with a digit
    # (degrees); compressed position always starts with a symbol table
    # ID ('/' or '\'), never a digit.
    probe = body[7:] if data_type in "/@" and len(body) >= 7 else body
    if not probe:
        return None
    if probe[0].isdigit():
        return _parse_uncompressed(data_type, body)
    if probe[0] in "/\\":
        return _parse_compressed(data_type, body)
    return None
