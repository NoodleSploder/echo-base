"""AIS (Automatic Identification System, marine VHF) decoder.

HDLC/NRZI framing identical to AX.25 -- same 0x7E flag, same 5-ones
bit-stuffing rule, same CRC-16/X-25 FCS (reused directly from
`ax25.compute_fcs`) -- but GMSK/9600-baud rather than AFSK1200 over
two audio tones. There's no "tone" to correlate here the way
`afsk.py` does: AIS's baseband bit signal *is* what
`dsp.fm_discriminator` already recovers (a frequency deviation whose
*sign* is the NRZI polarity), so bit recovery is a direct threshold
on the discriminator output rather than a mark/space energy
comparison. The bit-sync-by-brute-force-phase and NRZI/bit-destuffing
reasoning in `afsk.py`'s docstring applies here unchanged.

Message type + MMSI are always extracted (bits 0-5 and 8-37 of the
destuffed payload, MSB-first per ITU-R M.1371's own bit numbering --
distinct from the byte-packed, LSB-first representation the FCS check
uses, which is why this decoder keeps the destuffed bit list around
instead of only the packed bytes AX.25's decoder returns). Position
(latitude/longitude) is additionally extracted for Class A position
reports (message types 1/2/3) via `ais_position.parse_class_a_position`
-- unlike ADS-B, no frame-pairing is needed, since AIS packs a full
lat/lon into one message. Course, speed, and Class B (types 18/19,
a different bit layout) remain deliberately out of scope, same
"achievable subset first" reasoning as APRS/ADS-B's own gaps.
"""
from __future__ import annotations

import numpy as np

from app.services.decoders.ais_position import parse_class_a_position
from app.services.decoders.ax25 import compute_fcs

BAUD = 9600
_FLAG_BITS = "01111110"
_MAX_SEEN = 128
_MIN_PAYLOAD_BITS = 38  # message type (6) + MMSI (30), plus the 2-byte FCS


def _bits_to_int(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def _destuff(bits: list[int]) -> list[int] | None:
    destuffed: list[int] = []
    ones_run = 0
    i = 0
    while i < len(bits):
        bit = bits[i]
        if ones_run == 5:
            if bit != 0:
                return None  # bit-stuffing violation -- wrong phase, not a real frame
            ones_run = 0
            i += 1
            continue
        destuffed.append(bit)
        ones_run = ones_run + 1 if bit == 1 else 0
        i += 1
    return destuffed


def _pack_bytes_lsb_first(bits: list[int]) -> bytes | None:
    if len(bits) % 8 != 0 or not bits:
        return None
    out = bytearray()
    for start in range(0, len(bits), 8):
        value = 0
        for i, bit in enumerate(bits[start : start + 8]):
            value |= bit << i
        out.append(value)
    return bytes(out)


class AisDecoder:
    def __init__(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.samples_per_bit = sample_rate_hz / BAUD
        self._buffer = np.zeros(0, dtype=np.float32)
        # AIS frames are short (<~170ms even at max length) -- half a
        # second of history is generous margin, not a tuned constant.
        self._max_buffer_samples = int(sample_rate_hz * 0.5)
        self._seen: set[bytes] = set()
        self._seen_order: list[bytes] = []

    def feed(self, audio: np.ndarray) -> list[dict[str, object]]:
        """Returns newly-seen, FCS-valid messages as
        `{"message_type": ..., "mmsi": ...}`."""
        self._buffer = np.concatenate([self._buffer, audio.astype(np.float32)])
        if len(self._buffer) > self._max_buffer_samples:
            self._buffer = self._buffer[-self._max_buffer_samples :]

        spb = self.samples_per_bit
        phase_step = max(1, int(spb // 8))

        results: list[dict[str, object]] = []
        for phase in range(0, max(1, int(spb)), phase_step):
            bits = self._bits_from_signal(phase, spb)
            for destuffed in self._extract_valid_frames(bits):
                # `_seen` needs a hashable key -- destuffed is a bit list
                # (0/1 ints), so pack it to bytes just for dedup purposes.
                packed_key = _pack_bytes_lsb_first(destuffed) or b""
                if packed_key in self._seen:
                    continue
                self._seen.add(packed_key)
                self._seen_order.append(packed_key)
                if len(self._seen_order) > _MAX_SEEN:
                    oldest = self._seen_order.pop(0)
                    self._seen.discard(oldest)
                message: dict[str, object] = {
                    "message_type": _bits_to_int(destuffed[0:6]),
                    "mmsi": _bits_to_int(destuffed[8:38]),
                }
                position = parse_class_a_position(destuffed)
                if position is not None:
                    message["latitude"] = position.latitude
                    message["longitude"] = position.longitude
                results.append(message)
        return results

    def _bits_from_signal(self, phase: int, samples_per_bit: float) -> list[int]:
        centers: list[int] = []
        pos = phase + samples_per_bit / 2
        while pos < len(self._buffer):
            centers.append(int(pos))
            pos += samples_per_bit
        if len(centers) < 2:
            return []

        polarity = [self._buffer[c] > 0 for c in centers]
        bits = [1]
        bits.extend(0 if polarity[i] != polarity[i - 1] else 1 for i in range(1, len(polarity)))
        return bits

    @staticmethod
    def _extract_valid_frames(bits: list[int]) -> list[list[int]]:
        bitstring = "".join(map(str, bits))
        flag_positions = [i for i in range(len(bitstring) - 7) if bitstring[i : i + 8] == _FLAG_BITS]

        valid: list[list[int]] = []
        for i in range(len(flag_positions) - 1):
            start = flag_positions[i] + 8
            end = flag_positions[i + 1]
            if end <= start:
                continue
            destuffed = _destuff(bits[start:end])
            if destuffed is None or len(destuffed) < _MIN_PAYLOAD_BITS:
                continue

            payload_bits, fcs_bits = destuffed[:-16], destuffed[-16:]
            packed_payload = _pack_bytes_lsb_first(payload_bits)
            packed_fcs = _pack_bytes_lsb_first(fcs_bits)
            if packed_payload is None or packed_fcs is None:
                continue
            # FCS bytes, like every other HDLC byte, are packed LSB-first
            # (`_pack_bytes_lsb_first`, not the MSB-first `_bits_to_int`
            # payload fields use) -- and transmitted low-byte-first, same
            # convention `ax25.parse_ax25_frame` relies on.
            transmitted_fcs = packed_fcs[0] | (packed_fcs[1] << 8)
            if compute_fcs(packed_payload) != transmitted_fcs:
                continue
            valid.append(payload_bits)
        return valid
