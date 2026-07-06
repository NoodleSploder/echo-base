"""Parses APRS position reports (lat/lon) out of an AX.25 UI frame's info
field -- the payload `ax25.parse_ax25_frame` already extracts.

Only the "uncompressed" position format (APRS101.pdf ch. 8) is
supported: `!`/`=`/`/`/`@` followed by an 8-char latitude, a symbol
table ID, a 9-char longitude, a symbol code, and a free-text comment.
The compressed format (base-91 encoded, ch. 9) and Mic-E format
(position encoded in the *destination callsign*, ch. 10) are
structurally different enough to be their own follow-up rather than
squeezed into this parser -- both are common in real APRS traffic
(most modern trackers default to Mic-E), so this covers a real but
partial slice of position-bearing packets.
"""
from __future__ import annotations

from dataclasses import dataclass

_POSITION_DATA_TYPES = "!=/@"


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


def parse_aprs_position(info: bytes) -> AprsPosition | None:
    try:
        text = info.decode("ascii")
    except UnicodeDecodeError:
        return None

    if not text or text[0] not in _POSITION_DATA_TYPES:
        return None
    body = text[1:]

    if text[0] in "/@":
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
