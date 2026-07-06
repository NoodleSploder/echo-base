"""Mode S / ADS-B extended squitter decoder (1090MHz).

Deliberately narrower in scope than a full dump1090-equivalent: this
decodes DF17/18 extended squitters (the ADS-B broadcast format) down
to ICAO address + downlink format + ADS-B type code, validated by the
standard Mode S CRC-24. It does **not** decode callsigns (BDS 2,0
identification messages) or position (needs even/odd CPR frame
pairing across time, the same kind of complexity that made full APRS
position decoding partial too) -- both are natural follow-ups once
this baseline is confirmed working against real traffic, same
"ship the achievable subset first" pattern as `aprs_position.py`.

Unlike AFSK1200/SAME (audio-rate FSK/AFSK decoders fed demodulated
audio), Mode S is PPM (pulse position modulation) on the raw RF
envelope -- this decoder works directly on `abs(iq)`, at the
capture's native sample rate, not on anything StreamService
decimates down to 48kHz. It needs a genuinely wideband capture
(effectively 2MHz+, i.e. `set_sample_rate` to at least 2_000_000, and
tuned to 1090000000) to resolve the 0.5us pulse structure at all --
the default 240kHz spectrum/audio-oriented rate is nowhere close.
"""
from __future__ import annotations

import numpy as np

CRC_POLYNOMIAL = 0xFFF409  # standard Mode S CRC-24 generator
LONG_FRAME_BITS = 112
PREAMBLE_US = 8
_MAX_SEEN = 512


def crc24_remainder(message: bytes) -> int:
    """Mode S CRC-24 remainder over `message` (typically the full
    112-bit/14-byte frame, trailing 24-bit parity field included) --
    zero iff the frame (for DF17/18, which don't XOR in the address
    the way interrogation replies do) is uncorrupted.

    Bit-by-bit (not byte-table-optimized) on purpose: message lengths
    here are at most 112 bits, so the simplest-to-verify-correct form
    is plenty fast enough, and a byte-at-a-time optimization is an easy
    place to introduce an off-by-one in the bit ordering."""
    reg = 0
    for byte in message:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            top = (reg >> 23) & 1
            reg = ((reg << 1) & 0xFFFFFF) | bit
            if top:
                reg ^= CRC_POLYNOMIAL
    return reg


def _bits_to_bytes(bits: list[int]) -> bytes:
    n_bytes = len(bits) // 8
    out = bytearray(n_bytes)
    for i in range(n_bytes):
        value = 0
        for j in range(8):
            value = (value << 1) | bits[i * 8 + j]
        out[i] = value
    return bytes(out)


class ModeSDecoder:
    def __init__(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        # Samples per microsecond -- Mode S bits are 1us (PPM: pulse in
        # the first half-microsecond = "1", second half = "0"), so this
        # needs to be at least 2 for the two halves to be distinguishable
        # at all. Non-integer/odd values reduce accuracy (chip boundaries
        # don't land exactly on sample boundaries) but aren't rejected
        # outright -- same "best effort at whatever rate is configured"
        # approach `dsp.py`'s decimation already takes.
        self.samples_per_us = max(2, round(sample_rate_hz / 1_000_000))
        self.half_chip = max(1, self.samples_per_us // 2)
        self._buffer = np.zeros(0, dtype=np.float32)
        # Preamble + one long frame + a generous margin, in samples --
        # StreamService feeds chunks of raw samples repeatedly (not one
        # message at a time), so this needs enough slack that a message
        # straddling two chunks' worth of leading silence/other traffic
        # doesn't get its front edge trimmed off before it's ever seen
        # as a contiguous span.
        self._max_buffer_samples = (PREAMBLE_US + LONG_FRAME_BITS + 200) * self.samples_per_us
        self._seen: set[str] = set()
        self._seen_order: list[str] = []

    def feed(self, iq: np.ndarray) -> list[dict[str, object]]:
        """Returns newly-seen, CRC-valid messages as
        `{"hex": ..., "df": ..., "icao": ..., "type_code": ...}`."""
        mag = np.abs(iq).astype(np.float32)
        self._buffer = np.concatenate([self._buffer, mag])
        if len(self._buffer) > self._max_buffer_samples:
            self._buffer = self._buffer[-self._max_buffer_samples :]

        preamble_samples = PREAMBLE_US * self.samples_per_us
        message_samples = LONG_FRAME_BITS * self.samples_per_us
        # Largest `pos` for which a full preamble+message still fits.
        search_end = len(self._buffer) - preamble_samples - message_samples + 1

        results: list[dict[str, object]] = []
        pos = 0
        while pos < search_end:
            if self._is_preamble(pos):
                bits = self._decode_bits(pos + preamble_samples, LONG_FRAME_BITS)
                decoded = self._validate(bits)
                if decoded is not None and decoded["hex"] not in self._seen:
                    self._seen.add(decoded["hex"])
                    self._seen_order.append(decoded["hex"])
                    if len(self._seen_order) > _MAX_SEEN:
                        oldest = self._seen_order.pop(0)
                        self._seen.discard(oldest)
                    results.append(decoded)
                    pos += preamble_samples + message_samples
                    continue
            pos += 1
        return results

    def _is_preamble(self, pos: int) -> bool:
        # Pulses (0.5us each) at t=0, 1, 3.5, 4.5us -- in half-microsecond
        # "chip" units (each `half_chip` samples wide): chips 0, 2, 7, 9.
        # Everything else in the first 8us should be low.
        hc = self.half_chip
        idx = [pos + i * hc for i in range(10)]
        if idx[-1] + hc > len(self._buffer):
            return False
        vals = [float(self._buffer[i : i + hc].mean()) for i in idx]
        pulses = [vals[0], vals[2], vals[7], vals[9]]
        gaps = [vals[1], vals[3], vals[4], vals[5], vals[6], vals[8]]
        pulse_avg = sum(pulses) / 4
        if pulse_avg <= 1e-6:
            return False
        gap_avg = sum(gaps) / len(gaps)
        if gap_avg > pulse_avg * 0.5:
            return False
        return all(v > pulse_avg * 0.4 for v in pulses)

    def _decode_bits(self, start: int, n_bits: int) -> list[int]:
        hc = self.half_chip
        bits = []
        for i in range(n_bits):
            first = start + 2 * i * hc
            second = first + hc
            if second + hc > len(self._buffer):
                bits.append(0)
                continue
            first_energy = float(self._buffer[first:second].mean())
            second_energy = float(self._buffer[second : second + hc].mean())
            bits.append(1 if first_energy > second_energy else 0)
        return bits

    @staticmethod
    def _validate(bits: list[int]) -> dict[str, object] | None:
        frame = _bits_to_bytes(bits)
        if len(frame) != 14 or crc24_remainder(frame) != 0:
            return None

        df = bits[0] << 4 | bits[1] << 3 | bits[2] << 2 | bits[3] << 1 | bits[4]
        if df not in (17, 18):
            return None  # only extended squitters are in scope for this decoder

        icao = int.from_bytes(frame[1:4], "big")
        type_code = (frame[4] >> 3) & 0x1F  # first 5 bits of the 56-bit ME field

        return {
            "hex": frame.hex().upper(),
            "df": df,
            "icao": f"{icao:06X}",
            "type_code": type_code,
        }
