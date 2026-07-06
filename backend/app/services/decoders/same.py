"""NOAA Weather Radio SAME (Specific Area Message Encoding) decoder.

SAME is the format behind emergency/weather alert bursts on NOAA
Weather Radio and the Emergency Alert System. Simpler to decode than
AX.25/APRS in every way that matters here:

- Direct FSK, not differential (NRZI): the tone itself *is* the bit
  (mark=2083.3Hz="1", space=1562.5Hz="0"), no transition-comparison
  needed.
- No HDLC framing/bit-stuffing -- a message is a preamble (the byte
  0xAB repeated many times) followed directly by an ASCII header
  string starting with "ZCZC", sent three times per alert.

Same phase-offset brute-force approach as `afsk.py`'s AFSK1200 decoder
(exact bit-period boundaries aren't known in advance), but self-
rejection here relies on requiring a run of preamble bytes before
trusting a phase offset, rather than HDLC bit-stuffing.
"""
from __future__ import annotations

import re

import numpy as np

MARK_HZ = 2083.3  # binary 1
SPACE_HZ = 1562.5  # binary 0
BAUD = 520.83
PREAMBLE_BYTE = 0xAB
MIN_PREAMBLE_BYTES = 8
MAX_HEADER_LEN = 268  # per the SAME spec's maximum header length
_MAX_SEEN = 32


def parse_same_header(header: str) -> dict[str, object] | None:
    """Splits a raw "ZCZC-ORG-EEE-PSSCCC[-PSSCCC...]+TTTT-JJJHHMM-STATION-"
    header into its fields. Returns None if it doesn't structurally fit
    that shape (e.g. a truncated/corrupted decode)."""
    if not header.startswith("ZCZC-") or "+" not in header:
        return None
    body = header[len("ZCZC-") :]
    codes_part, _, rest = body.partition("+")
    fields = codes_part.split("-")
    if len(fields) < 3:
        return None
    originator, event_code, *locations = fields

    rest_fields = rest.split("-")
    if len(rest_fields) < 3:
        return None
    purge_time, timestamp, station = rest_fields[0], rest_fields[1], rest_fields[2]

    return {
        "originator": originator,
        "event_code": event_code,
        "locations": locations,
        "purge_time": purge_time,
        "timestamp": timestamp,
        "station": station,
    }


def _extract_header(text: str) -> str | None:
    # `errors="ignore"` decoding already drops non-ASCII bytes; this just
    # bounds the match to the printable run starting at "ZCZC" -- in
    # practice that run ends right at the real header's trailing '-'
    # since whatever follows a SAME burst (silence, the next repeat's
    # preamble, station audio) decodes to non-printable/control bytes.
    match = re.search(r"ZCZC[\x20-\x7E]*", text)
    return match.group(0) if match else None


class SameDecoder:
    def __init__(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.samples_per_bit = sample_rate_hz / BAUD
        kernel_len = max(4, int(round(self.samples_per_bit)))
        t = np.arange(kernel_len)
        # A Hann-windowed kernel is not optional here the way it would be
        # for AFSK1200: SAME's tone spacing (~520Hz) exactly equals the
        # baud rate, which is the worst case for a rectangular-window
        # matched filter (its sidelobes leak enough between the two tones
        # to make them nearly indistinguishable). Windowing suppresses
        # those sidelobes at the cost of a slightly wider main lobe --
        # confirmed against a synthetic round trip: unwindowed kernels
        # decoded ~74% of bits correctly (i.e. useless); Hann-windowed
        # kernels of the same length decoded 695/696.
        window = np.hanning(kernel_len).astype(np.float32)
        self._mark_cos = np.cos(2 * np.pi * MARK_HZ * t / sample_rate_hz).astype(np.float32) * window
        self._mark_sin = np.sin(2 * np.pi * MARK_HZ * t / sample_rate_hz).astype(np.float32) * window
        self._space_cos = np.cos(2 * np.pi * SPACE_HZ * t / sample_rate_hz).astype(np.float32) * window
        self._space_sin = np.sin(2 * np.pi * SPACE_HZ * t / sample_rate_hz).astype(np.float32) * window

        self._buffer = np.zeros(0, dtype=np.float32)
        self._max_buffer_samples = int(sample_rate_hz * 6)  # a header can take ~4s to send
        self._seen: set[str] = set()
        self._seen_order: list[str] = []

    def feed(self, audio: np.ndarray) -> list[str]:
        """Returns newly-seen SAME header strings (e.g. "ZCZC-WXR-RWT-...-")."""
        self._buffer = np.concatenate([self._buffer, audio.astype(np.float32)])
        if len(self._buffer) > self._max_buffer_samples:
            self._buffer = self._buffer[-self._max_buffer_samples :]

        tone = self._tone_signal(self._buffer)
        spb = self.samples_per_bit
        phase_step = max(1, int(spb // 8))

        new_headers: list[str] = []
        for phase in range(0, max(1, int(spb)), phase_step):
            bits = self._bits_from_tone(tone, phase, spb)
            header = self._decode_header(bits)
            if header and header not in self._seen:
                self._seen.add(header)
                self._seen_order.append(header)
                if len(self._seen_order) > _MAX_SEEN:
                    oldest = self._seen_order.pop(0)
                    self._seen.discard(oldest)
                new_headers.append(header)
        return new_headers

    def _tone_signal(self, audio: np.ndarray) -> np.ndarray:
        mark_i = np.convolve(audio, self._mark_cos, mode="valid")
        mark_q = np.convolve(audio, self._mark_sin, mode="valid")
        space_i = np.convolve(audio, self._space_cos, mode="valid")
        space_q = np.convolve(audio, self._space_sin, mode="valid")
        mark_energy = np.hypot(mark_i, mark_q)
        space_energy = np.hypot(space_i, space_q)
        return mark_energy - space_energy  # > 0 => mark ("1"), < 0 => space ("0")

    @staticmethod
    def _bits_from_tone(tone: np.ndarray, phase: int, samples_per_bit: float) -> list[int]:
        bits = []
        pos = phase + samples_per_bit / 2
        while pos < len(tone):
            bits.append(1 if tone[int(pos)] > 0 else 0)
            pos += samples_per_bit
        return bits

    @staticmethod
    def _decode_header(bits: list[int]) -> str | None:
        if len(bits) < MIN_PREAMBLE_BYTES * 8:
            return None

        # Pack LSB-first bytes, same bit order as AX.25/most async serial framing.
        byte_count = len(bits) // 8
        bytes_out = bytearray(byte_count)
        for i in range(byte_count):
            value = 0
            for bit_index in range(8):
                value |= bits[i * 8 + bit_index] << bit_index
            bytes_out[i] = value

        # Require a real run of preamble bytes before trusting this phase --
        # this is what rejects wrong bit-sync guesses, the way HDLC
        # bit-stuffing does for the AX.25 decoder.
        preamble_run = 0
        start = 0
        for i, byte in enumerate(bytes_out):
            if byte == PREAMBLE_BYTE:
                preamble_run += 1
                if preamble_run >= MIN_PREAMBLE_BYTES:
                    start = i + 1
                    break
            else:
                preamble_run = 0
        else:
            return None

        candidate = bytes(bytes_out[start : start + MAX_HEADER_LEN])
        text = candidate.decode("ascii", errors="ignore")
        return _extract_header(text)
