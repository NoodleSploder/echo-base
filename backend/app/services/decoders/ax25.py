"""AX.25 frame parsing (addresses, FCS, APRS info field) -- the packet
layer riding on top of the AFSK1200 bit stream `afsk.py` recovers.

Reference: AX.25 Link Access Protocol v2.2. Only UI frames (what APRS
uses) are meaningfully decoded; other control-field values are still
parsed structurally but not interpreted.
"""
from __future__ import annotations

from dataclasses import dataclass

# AX.25 FCS: CRC-16/X-25 (poly 0x8408 reflected), init 0xFFFF, result inverted.
_FCS_POLY = 0x8408


def compute_fcs(data: bytes) -> int:
    fcs = 0xFFFF
    for byte in data:
        fcs ^= byte
        for _ in range(8):
            if fcs & 1:
                fcs = (fcs >> 1) ^ _FCS_POLY
            else:
                fcs >>= 1
    return fcs ^ 0xFFFF


@dataclass
class Ax25Address:
    callsign: str
    ssid: int
    has_been_repeated: bool = False


@dataclass
class Ax25Frame:
    destination: Ax25Address
    source: Ax25Address
    digipeaters: list[Ax25Address]
    control: int
    pid: int
    info: bytes


def _decode_address(raw: bytes) -> tuple[Ax25Address, bool]:
    """Decodes one 7-byte AX.25 address field. Returns (address, is_last)."""
    callsign = "".join(chr((raw[i] >> 1) & 0x7F) for i in range(6)).strip()
    ssid_byte = raw[6]
    ssid = (ssid_byte >> 1) & 0x0F
    has_been_repeated = bool(ssid_byte & 0x80)
    is_last = bool(ssid_byte & 0x01)
    return Ax25Address(callsign=callsign, ssid=ssid, has_been_repeated=has_been_repeated), is_last


def parse_ax25_frame(frame: bytes) -> Ax25Frame | None:
    """Parses a de-stuffed AX.25 frame (flags already stripped) whose
    trailing 2 bytes are the transmitted FCS. Returns None if too short
    or the FCS doesn't check out."""
    if len(frame) < 2 + 14 + 1 + 1:  # FCS + dest/src addresses + control + PID
        return None

    payload, fcs_bytes = frame[:-2], frame[-2:]
    transmitted_fcs = fcs_bytes[0] | (fcs_bytes[1] << 8)
    if compute_fcs(payload) != transmitted_fcs:
        return None

    if len(payload) < 14:
        return None

    destination, _ = _decode_address(payload[0:7])
    source, source_is_last = _decode_address(payload[7:14])

    offset = 14
    digipeaters: list[Ax25Address] = []
    is_last = source_is_last
    while not is_last:
        if offset + 7 > len(payload):
            return None
        addr, is_last = _decode_address(payload[offset : offset + 7])
        digipeaters.append(addr)
        offset += 7

    if offset >= len(payload):
        return None
    control = payload[offset]
    offset += 1

    # UI frames (APRS) carry a PID byte; not all control values do, but
    # every APRS packet is a UI frame (control == 0x03) so this is safe
    # for the traffic this decoder cares about.
    pid = payload[offset] if offset < len(payload) else 0
    offset += 1
    info = payload[offset:]

    return Ax25Frame(
        destination=destination,
        source=source,
        digipeaters=digipeaters,
        control=control,
        pid=pid,
        info=info,
    )


def format_path(frame: Ax25Frame) -> str:
    parts = [f"{d.callsign}-{d.ssid}" if d.ssid else d.callsign for d in frame.digipeaters]
    return ",".join(parts)


def format_callsign(address: Ax25Address) -> str:
    return f"{address.callsign}-{address.ssid}" if address.ssid else address.callsign
