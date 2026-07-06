"""SSTV (Slow-Scan Television) decoder -- Martin M1 mode.

SSTV encodes a picture as a series of audio tones: within each scan
line, instantaneous frequency directly represents pixel brightness
(1500Hz = black, 2300Hz = white), separated by a distinctive 1200Hz
sync pulse marking where each line begins. It's exactly the same kind
of "frequency IS the data" signal AFSK1200/Mode S are, just carrying a
picture instead of packets -- and, like those decoders, this operates
on already-FM-demodulated audio (`dsp.fm_discriminator`'s output), not
raw IQ.

Scope: **Martin M1 only** (320x256, RGB scan order G/B/R) -- one of the
oldest and most commonly implemented SSTV modes, and the natural
"achievable subset first" choice (same reasoning as `mode_s.py`
picking DF17/18 airborne position before surface position/callsigns).
Other modes (Scottie, Robot 36, PD120 -- the mode the ISS actually
uses for its periodic SSTV events) share the same "sync pulse + per-
pixel frequency-as-brightness" shape but different timing/channel-
order tables, and would be a natural follow-up.

Two-stage frequency recovery, same shape as AFSK1200's "tone
correlation on top of an already-demodulated signal": the FM
discriminator recovers the audio baseband (an instant Hz reading), and
this then recovers *that audio's own* instantaneous frequency (the
SSTV tone, 1200-2300Hz) via a discrete Hilbert transform -- the
standard analytic-signal technique, implemented directly with
`numpy.fft` here rather than pulling in scipy for one function.

**Known limitation, honestly documented rather than silently
tolerated**: sync-pulse tracking is a narrow-window search anchored
right after the previous line (see `_try_decode_one_line`), which
avoids the far more common failure mode of locking onto a spurious
sync-band dip inside a later line's own picture content (real images
routinely have near-black pixels close enough to the 1200Hz sync tone
that Hilbert-transform noise briefly dips below the threshold used to
tell them apart). The trade-off: on rare occasions the *real* next
sync pulse drifts slightly outside that narrow window (accumulated
timing imprecision over many lines), and the decoder falls back to a
wider search that can, rarely, skip an entire line rather than
mis-decoding one. In practice this means a full 256-line image
typically decodes in the mid-to-high 90% range of its lines correctly
rather than a deterministic 100% -- a reasonable trade for a bonus
feature, not something a production broadcast/aviation decoder in
this same codebase (Mode S, AIS) would accept.
"""
from __future__ import annotations

import numpy as np

WIDTH = 320
HEIGHT = 256
SYNC_HZ = 1200.0
BLACK_HZ = 1500.0
WHITE_HZ = 2300.0
SYNC_DURATION_S = 0.004862
SYNC_PORCH_S = 0.000572
CHANNEL_SCAN_S = 0.146432
CHANNEL_ORDER = ("G", "B", "R")  # Martin M1 transmits green, then blue, then red, per line
_CHANNEL_TO_RGB_INDEX = {"R": 0, "G": 1, "B": 2}

# A sync pulse lasting at least this fraction of the nominal duration
# still counts -- real audio has noisy transitions at tone boundaries,
# so requiring the full nominal length would miss genuine pulses.
_MIN_SYNC_FRACTION = 0.6
# Sync (1200Hz) vs. the lowest real picture tone (black, 1500Hz) has a
# clean 300Hz gap -- anything below this threshold is "sync-like".
_SYNC_BAND_HZ = 1350.0


def hz_to_luma(freq_hz: np.ndarray) -> np.ndarray:
    """Vectorized black(1500Hz)-to-white(2300Hz) -> 0-255 mapping,
    clipping anything outside that range rather than wrapping/erroring
    -- real demodulated audio routinely overshoots the nominal band."""
    clipped = np.clip(freq_hz, BLACK_HZ, WHITE_HZ)
    return (((clipped - BLACK_HZ) / (WHITE_HZ - BLACK_HZ)) * 255).astype(np.uint8)


def _hilbert_analytic(x: np.ndarray) -> np.ndarray:
    """The analytic signal (a + jb, where b is x's Hilbert transform)
    via the standard FFT construction -- exactly what `scipy.signal.
    hilbert` does, reimplemented directly since it's the only thing
    that would need scipy as a dependency."""
    n = len(x)
    spectrum = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1
        h[1 : n // 2] = 2
    else:
        h[0] = 1
        h[1 : (n + 1) // 2] = 2
    return np.fft.ifft(spectrum * h)


def instantaneous_frequency_hz(audio: np.ndarray, sample_rate_hz: int) -> np.ndarray:
    """Per-sample instantaneous frequency of a real-valued signal, via
    its analytic signal's unwrapped phase derivative. Same length as
    `audio` (the last sample repeats the second-to-last, since a phase
    *derivative* is one sample shorter than the phase itself)."""
    if len(audio) < 2:
        return np.zeros(len(audio), dtype=np.float32)
    analytic = _hilbert_analytic(audio.astype(np.float64))
    phase = np.unwrap(np.angle(analytic))
    inst_freq = np.diff(phase) * sample_rate_hz / (2 * np.pi)
    return np.concatenate([inst_freq, inst_freq[-1:]]).astype(np.float32)


def find_sync_pulse(freq_hz: np.ndarray, sample_rate_hz: int) -> int | None:
    """The start index of the first run of sync-band frequency lasting
    at least `_MIN_SYNC_FRACTION` of a nominal sync pulse -- None if no
    such run exists yet (the caller should wait for more data)."""
    sync_band = freq_hz < _SYNC_BAND_HZ
    min_run = int(SYNC_DURATION_S * _MIN_SYNC_FRACTION * sample_rate_hz)
    padded = np.concatenate(([0], sync_band.astype(np.int8), [0]))
    edges = np.diff(padded)
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    for start, end in zip(starts, ends, strict=True):
        if end - start >= min_run:
            return int(start)
    return None


class MartinM1Decoder:
    """Stateful, streaming decoder -- same "grow a buffer, consume
    whatever's fully decodable, keep the remainder" shape as
    `mode_s.ModeSDecoder`. `feed(audio)` can be called with arbitrarily
    small chunks (matches the ~20-100ms chunks `stream_service.py`
    already produces for every other decoder)."""

    def __init__(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        self._sync_len = round(SYNC_DURATION_S * sample_rate_hz)
        self._porch_len = round(SYNC_PORCH_S * sample_rate_hz)
        self._channel_len = round(CHANNEL_SCAN_S * sample_rate_hz)
        self._line_len = self._sync_len + 3 * self._porch_len + 3 * self._channel_len
        # ~2ms tolerance on the "enough buffer for a whole line" check
        # -- see _try_decode_one_line for why the last line of an
        # image needs this.
        self._line_len_tolerance = max(1, round(0.002 * sample_rate_hz))
        # A few lines' worth of margin -- enough that a sync pulse
        # search always has a full line available once it finds one,
        # without accumulating the entire (multi-minute) transmission.
        # Generous on purpose: the Hilbert transform is less accurate
        # right at whatever's currently the *end* of the buffer, which
        # can occasionally suppress a genuine sync pulse for a buffer
        # or two until more data arrives and it's no longer right at
        # the edge -- too small a margin here would let the "buffer
        # grew too large without a sync" safety trim (in `feed`)
        # discard that pulse for good before it's ever found.
        self._max_buffer_samples = self._line_len * 8

        self._buffer = np.zeros(0, dtype=np.float32)
        self.image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.lines_decoded = 0
        # Whether at least one real sync pulse has been found yet --
        # see _try_decode_one_line for why this narrows where
        # subsequent searches look.
        self._synced_once = False

    @property
    def is_complete(self) -> bool:
        return self.lines_decoded >= HEIGHT

    def feed(self, audio: np.ndarray) -> int:
        """Returns how many new lines were decoded from this call."""
        self._buffer = np.concatenate([self._buffer, audio.astype(np.float32)])
        new_lines = 0
        # The tolerance here mirrors _try_decode_one_line's own check
        # (see there for why) -- this is just a cheap pre-filter so
        # tiny buffers don't pay for a Hilbert transform + sync search
        # that's certain to come back "not enough data yet".
        while (
            len(self._buffer) >= self._line_len - self._line_len_tolerance
            and self._try_decode_one_line()
        ):
            new_lines += 1
        # No sync found in an unreasonably large buffer -- drop the
        # oldest excess rather than searching an ever-growing buffer
        # (e.g. silence/noise with no real SSTV signal present at all).
        if len(self._buffer) > self._max_buffer_samples * 4:
            self._buffer = self._buffer[-self._max_buffer_samples :]
        return new_lines

    def _try_decode_one_line(self) -> bool:
        if self.is_complete:
            # A prior image finished -- a new transmission starting
            # fresh overwrites it rather than appending past the bottom.
            self.image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            self.lines_decoded = 0
            self._synced_once = False  # a new transmission may have a VIS header/gap first

        freq = instantaneous_frequency_hz(self._buffer, self.sample_rate_hz)
        if self._synced_once:
            # Every line after the first starts the buffer right where
            # the previous one was trimmed off -- so the true next sync
            # pulse is expected right near the start, and searching
            # only a narrow window there (rather than the whole,
            # possibly multi-line, buffer) avoids locking onto a
            # spurious sync-band dip inside a *later* line's real
            # picture content (real images routinely have near-black
            # pixels close enough to the sync threshold that
            # Hilbert-transform noise can briefly dip below it).
            search_limit = self._sync_len + 4 * self._line_len_tolerance
            sync_start = find_sync_pulse(freq[:search_limit], self.sample_rate_hz)
            if sync_start is None and len(freq) > self._line_len + search_limit:
                # Not where expected even with a full line's worth of
                # slack -- something drifted more than anticipated
                # (rounding, real transmitter clock drift, etc.).
                # Falling back to a full search re-syncs rather than
                # getting stuck here forever; the narrow search above
                # is still what's used on every normal line.
                sync_start = find_sync_pulse(freq, self.sample_rate_hz)
        else:
            sync_start = find_sync_pulse(freq, self.sample_rate_hz)
        if sync_start is None:
            return False
        # A few samples' tolerance: the Hilbert transform is slightly
        # less accurate right at the edge of whatever's been buffered
        # so far, which can place a *trailing* sync pulse (the
        # transmission's last line, with nothing after it to anchor
        # against) a handful of samples later than the true nominal
        # position. Without this, the last line of an image would
        # never decode -- there's no "next" pulse to eventually prove
        # enough data has arrived.
        if sync_start + self._line_len - self._line_len_tolerance > len(self._buffer):
            return False  # a real pulse, but not enough buffered yet for the whole line

        self._synced_once = True
        self.image[self.lines_decoded] = self._decode_line(freq, sync_start)
        self.lines_decoded += 1
        self._buffer = self._buffer[sync_start + self._line_len :]
        return True

    def _decode_line(self, freq: np.ndarray, sync_start: int) -> np.ndarray:
        row = np.zeros((WIDTH, 3), dtype=np.uint8)
        offset = self._sync_len + self._porch_len  # green channel starts right after the first porch
        for channel in CHANNEL_ORDER:
            segment = freq[sync_start + offset : sync_start + offset + self._channel_len]
            row[:, _CHANNEL_TO_RGB_INDEX[channel]] = self._decode_channel(segment)
            offset += self._channel_len + self._porch_len
        return row

    @staticmethod
    def _decode_channel(segment: np.ndarray) -> np.ndarray:
        n = len(segment)
        if n < WIDTH:
            return np.zeros(WIDTH, dtype=np.uint8)
        # `n / WIDTH` (~11.0 samples/pixel for a 320px channel at 48kHz)
        # is essentially never a whole number -- a fixed-size reshape
        # (`n // WIDTH` samples per pixel, discarding the remainder)
        # would silently misalign more and more with each pixel across
        # the row, since the *true* per-pixel boundary drifts by a
        # fraction of a sample every time. Exact (fractional) boundary
        # edges avoid that drift entirely.
        edges = np.round(np.linspace(0, n, WIDTH + 1)).astype(np.int64)
        sums = np.add.reduceat(segment, edges[:-1])
        counts = np.maximum(np.diff(edges), 1)
        pixel_freqs = sums / counts
        return hz_to_luma(pixel_freqs)
