"""Bell 202 AFSK1200 demodulator for AX.25/APRS over already-FM-demodulated audio.

This takes the same discriminator output `dsp.fm_discriminator` produces
(the "audio" a real TNC's input would see) and recovers raw, still-
bit-stuffed AX.25 frames (HDLC flags stripped, FCS still attached --
`ax25.parse_ax25_frame` verifies and strips it).

Approach, in short:

1. Correlate the audio against 1200Hz ("mark") and 2200Hz ("space")
   tones over a sliding window the length of one bit period, giving a
   continuous "which tone is stronger" signal.
2. AX.25 encodes bits differentially (NRZI): a tone *change* between
   consecutive bit periods is a 0 bit, no change is a 1 bit. Sampling
   the tone signal once per bit period and comparing to the previous
   sample recovers the bit stream -- *given* the bit-period boundaries
   are known.
3. Bit-period boundaries (the "phase") aren't known in advance, so a
   handful of candidate phase offsets are tried per buffer; wrong
   offsets produce bit garbage that (thanks to HDLC bit-stuffing
   making 6 consecutive 1-bits impossible in real data) essentially
   never lines up with a valid flag+FCS, so they're self-rejecting.

No continuous clock-recovery PLL: samples-per-bit is a fixed constant
(audio rate / 1200), which only drifts against the real transmitter's
independent clock by a few microseconds over one packet's duration --
negligible at 1200 baud. This is a simplification that would need
revisiting for very long frames or non-nominal audio rates.
"""
from __future__ import annotations

import numpy as np

MARK_HZ = 1200
SPACE_HZ = 2200
BAUD = 1200
_FLAG_BITS = "01111110"
_MAX_SEEN_FRAMES = 64


class Afsk1200Decoder:
    def __init__(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.samples_per_bit = sample_rate_hz / BAUD
        kernel_len = max(4, int(round(self.samples_per_bit)))
        t = np.arange(kernel_len)
        self._mark_cos = np.cos(2 * np.pi * MARK_HZ * t / sample_rate_hz).astype(np.float32)
        self._mark_sin = np.sin(2 * np.pi * MARK_HZ * t / sample_rate_hz).astype(np.float32)
        self._space_cos = np.cos(2 * np.pi * SPACE_HZ * t / sample_rate_hz).astype(np.float32)
        self._space_sin = np.sin(2 * np.pi * SPACE_HZ * t / sample_rate_hz).astype(np.float32)

        self._buffer = np.zeros(0, dtype=np.float32)
        self._max_buffer_samples = int(sample_rate_hz * 2)  # ~2s of history
        self._seen_frames: set[bytes] = set()
        self._seen_order: list[bytes] = []

    def feed(self, audio: np.ndarray) -> list[bytes]:
        """Returns newly-seen raw AX.25 frames (still carrying their FCS,
        not yet verified) found since the last call."""
        self._buffer = np.concatenate([self._buffer, audio.astype(np.float32)])
        if len(self._buffer) > self._max_buffer_samples:
            self._buffer = self._buffer[-self._max_buffer_samples :]

        tone = self._tone_signal(self._buffer)
        spb = self.samples_per_bit
        phase_step = max(1, int(spb // 8))

        new_frames: list[bytes] = []
        for phase in range(0, max(1, int(spb)), phase_step):
            bits = self._bits_from_tone(tone, phase, spb)
            for frame in self._extract_frames(bits):
                if frame in self._seen_frames:
                    continue
                self._seen_frames.add(frame)
                self._seen_order.append(frame)
                if len(self._seen_order) > _MAX_SEEN_FRAMES:
                    oldest = self._seen_order.pop(0)
                    self._seen_frames.discard(oldest)
                new_frames.append(frame)
        return new_frames

    def _tone_signal(self, audio: np.ndarray) -> np.ndarray:
        mark_i = np.convolve(audio, self._mark_cos, mode="valid")
        mark_q = np.convolve(audio, self._mark_sin, mode="valid")
        space_i = np.convolve(audio, self._space_cos, mode="valid")
        space_q = np.convolve(audio, self._space_sin, mode="valid")
        mark_energy = np.hypot(mark_i, mark_q)
        space_energy = np.hypot(space_i, space_q)
        return space_energy - mark_energy  # > 0 => space dominant, < 0 => mark dominant

    @staticmethod
    def _bits_from_tone(tone: np.ndarray, phase: int, samples_per_bit: float) -> list[int]:
        centers: list[int] = []
        pos = phase + samples_per_bit / 2
        while pos < len(tone):
            centers.append(int(pos))
            pos += samples_per_bit
        if len(centers) < 2:
            return []

        polarity = [tone[c] > 0 for c in centers]
        # bits[0] is a placeholder -- there's no known prior polarity before
        # the buffer starts, so it can't be derived from data. Every bit
        # after it is a real NRZI-decoded value relative to its predecessor.
        bits = [1]
        bits.extend(0 if polarity[i] != polarity[i - 1] else 1 for i in range(1, len(polarity)))
        return bits

    def _extract_frames(self, bits: list[int]) -> list[bytes]:
        bitstring = "".join(map(str, bits))
        flag_positions = [i for i in range(len(bitstring) - 7) if bitstring[i : i + 8] == _FLAG_BITS]

        frames: list[bytes] = []
        for i in range(len(flag_positions) - 1):
            start = flag_positions[i] + 8
            end = flag_positions[i + 1]
            if end <= start:
                continue
            frame_bytes = self._destuff_and_pack(bits[start:end])
            if frame_bytes is not None:
                frames.append(frame_bytes)
        return frames

    @staticmethod
    def _destuff_and_pack(bits: list[int]) -> bytes | None:
        destuffed: list[int] = []
        ones_run = 0
        i = 0
        while i < len(bits):
            bit = bits[i]
            if ones_run == 5:
                if bit != 0:
                    return None  # bit-stuffing violation: not a real frame at this phase
                ones_run = 0
                i += 1
                continue
            destuffed.append(bit)
            ones_run = ones_run + 1 if bit == 1 else 0
            i += 1

        if len(destuffed) % 8 != 0 or not destuffed:
            return None

        out = bytearray()
        for byte_start in range(0, len(destuffed), 8):
            value = 0
            for bit_index, bit in enumerate(destuffed[byte_start : byte_start + 8]):
                value |= bit << bit_index  # AX.25 transmits each byte LSB-first
            out.append(value)
        return bytes(out)
