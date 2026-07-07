"""FT8 standard message (type i3=1/2) unpacking: two callsigns + a
grid locator or signal report, from the 77-bit payload the LDPC
decoder recovers.

Ported from ft8_lib's `message.c` (`ftx_message_decode_std`,
`unpack28`, `unpackgrid`) and `text.c` (`charn`) -- verified against
that exact C implementation by compiling it and comparing payload
bytes for known messages (see `test_ft8_message.py`), not just
re-derived from the protocol description.

Scope: **standard messages only** (i3 in {1, 2} -- two callsigns, an
optional `/R` or `/P` suffix, and a grid locator or a signal report).
Free text, telemetry, DXpedition mode, and hashed/non-standard
callsigns are all real FT8 message types this project doesn't decode
yet -- the same "achievable subset first" reasoning as every other
decoder gap in this codebase. A message of an unsupported type
(including one whose CRC fails, e.g. a genuine decode error) returns
None rather than a wrong guess.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.decoders.ft8_constants import (
    CHAR_TABLE_ALPHANUM,
    CHAR_TABLE_ALPHANUM_SPACE,
    CHAR_TABLE_LETTERS_SPACE,
    CHAR_TABLE_NUMERIC,
    MAX22,
    MAXGRID4,
    NTOKENS,
)


@dataclass(frozen=True)
class Ft8StandardMessage:
    call_to: str
    call_de: str
    extra: str  # grid locator, signal report, or a token like "RRR"/"73"


def _bits_to_int(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def _charn(index: int, table: str) -> str:
    return table[index]


def _unpack28(n28: int, has_suffix: bool, i3: int) -> str | None:
    """`n28` is the 28-bit callsign field (already separated from its
    1-bit suffix-flag LSB). Returns None for anything this decoder
    doesn't cover (a 22-bit hashed callsign -- needs a hash table this
    project doesn't build -- or a malformed token)."""
    if n28 < NTOKENS:
        if n28 <= 2:
            return ("DE", "QRZ", "CQ")[n28]
        if n28 <= 1002:
            return f"CQ {n28 - 3:03d}"
        if n28 <= 532_443:
            n = n28 - 1003
            chars = []
            for _ in range(4):
                chars.append(_charn(n % 27, CHAR_TABLE_LETTERS_SPACE))
                n //= 27
            return "CQ " + "".join(reversed(chars)).strip()
        return None

    n28 -= NTOKENS
    if n28 < MAX22:
        return None  # a 22-bit hashed callsign -- no hash table in this project yet

    n = n28 - MAX22
    chars = [""] * 6
    chars[5] = _charn(n % 27, CHAR_TABLE_LETTERS_SPACE)
    n //= 27
    chars[4] = _charn(n % 27, CHAR_TABLE_LETTERS_SPACE)
    n //= 27
    chars[3] = _charn(n % 27, CHAR_TABLE_LETTERS_SPACE)
    n //= 27
    chars[2] = _charn(n % 10, CHAR_TABLE_NUMERIC)
    n //= 10
    chars[1] = _charn(n % 36, CHAR_TABLE_ALPHANUM)
    n //= 36
    chars[0] = _charn(n % 37, CHAR_TABLE_ALPHANUM_SPACE)

    callsign = "".join(chars)
    if callsign.startswith("3D0") and callsign[3] != " ":
        result = "3DA0" + callsign[3:].strip()
    elif callsign[0] == "Q" and callsign[1].isalpha():
        result = "3X" + callsign[1:].strip()
    else:
        result = callsign.strip()

    if len(result) < 3:
        return None

    if has_suffix:
        if i3 == 1:
            result += "/R"
        elif i3 == 2:
            result += "/P"
        else:
            return None
    return result


def _unpackgrid(igrid4: int, has_r_prefix: bool) -> str | None:
    if igrid4 <= MAXGRID4:
        n = igrid4
        d = "0" + str(n % 10)
        n //= 10
        c = "0" + str(n % 10)
        n //= 10
        b = chr(ord("A") + n % 18)
        n //= 18
        a = chr(ord("A") + n % 18)
        grid = f"{a}{b}{c[-1]}{d[-1]}"
        return ("R " + grid) if has_r_prefix else grid

    report = igrid4 - MAXGRID4
    if report == 1:
        return ""
    if report == 2:
        return "RRR"
    if report == 3:
        return "RR73"
    if report == 4:
        return "73"
    value = report - 35
    sign = "+" if value >= 0 else "-"
    prefix = "R" if has_r_prefix else ""
    return f"{prefix}{sign}{abs(value):02d}"


def get_i3(payload_bits: list[int]) -> int:
    """`payload_bits` is the 77-bit message payload (CRC already
    stripped/verified separately). i3 occupies bits 74-76."""
    assert len(payload_bits) == 77
    return _bits_to_int(payload_bits[74:77])


def unpack_standard_message(payload_bits: list[int]) -> Ft8StandardMessage | None:
    """None if this isn't a standard (i3 in {1, 2}) message, or if it
    uses a feature this decoder doesn't cover (a hashed callsign)."""
    assert len(payload_bits) == 77
    i3 = get_i3(payload_bits)
    if i3 not in (1, 2):
        return None

    n29a = _bits_to_int(payload_bits[0:29])
    n29b = _bits_to_int(payload_bits[29:58])
    ir = payload_bits[58]
    igrid4 = _bits_to_int(payload_bits[59:74])

    call_to = _unpack28(n29a >> 1, bool(n29a & 1), i3)
    call_de = _unpack28(n29b >> 1, bool(n29b & 1), i3)
    if call_to is None or call_de is None:
        return None
    extra = _unpackgrid(igrid4, bool(ir))
    if extra is None:
        return None
    return Ft8StandardMessage(call_to=call_to, call_de=call_de, extra=extra)


def grid_to_lat_lon(grid: str) -> tuple[float, float] | None:
    """Maidenhead grid locator -> (lat, lon) of the grid square's
    *centroid* -- FT8 only ever conveys a 4-character locator (about
    ~150km x ~300km at mid-latitudes), so this is deliberately a
    coarse position, the same resolution every real FT8 spotting map
    (e.g. PSKReporter) shows. Returns None for anything that isn't a
    plain 4-character grid (e.g. "RRR", "-12", "R FN42" with its
    prefix not stripped by the caller)."""
    grid = grid.strip().upper()
    if len(grid) != 4 or not (grid[0].isalpha() and grid[1].isalpha()):
        return None
    if not (grid[2].isdigit() and grid[3].isdigit()):
        return None
    field_lon = ord(grid[0]) - ord("A")
    field_lat = ord(grid[1]) - ord("A")
    square_lon = int(grid[2])
    square_lat = int(grid[3])
    if not (0 <= field_lon < 18 and 0 <= field_lat < 18):
        return None

    lon = field_lon * 20 - 180 + square_lon * 2 + 1  # +1: centroid of the 2deg-wide square
    lat = field_lat * 10 - 90 + square_lat * 1 + 0.5  # +0.5: centroid of the 1deg-tall square
    return lat, lon
