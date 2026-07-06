"""Peak detection over an FFT magnitude array (Phase 4: signal detection
/ peak analysis).

Kept as pure functions/a small stateful tracker, separate from
stream_service.py's threading and broadcast plumbing, so the actual
peak-finding logic can be unit tested directly against synthetic
spectra.
"""
from __future__ import annotations

import numpy as np


def estimate_noise_floor_db(magnitude_db: np.ndarray) -> float:
    """Median magnitude across the spectrum. Verified live against a real
    RTL-SDR: this FFT's dB scale is `20*log10(raw ADC magnitude)`, not
    calibrated to any physical reference (dBm/dBFS/etc.) -- it shifts
    with gain, sample rate, and windowing. An *absolute* threshold_db
    therefore only "works" for whatever gain happened to be set when it
    was chosen: at one gain setting -30dB caught nothing, at another it
    flagged nearly the entire spectrum as one continuous peak. The
    median is robust to the handful of bins an actual signal occupies
    (unlike the mean, which a strong peak skews upward) and gives a
    threshold that adapts to gain/hardware automatically."""
    return float(np.median(magnitude_db))


def find_peak_bins(magnitude_db: np.ndarray, margin_db: float) -> set[int]:
    """Bins that are local maxima at least `margin_db` above the
    spectrum's own estimated noise floor. A "local maximum" is a bin
    whose magnitude is >= both neighbors -- this finds the center of
    every distinct signal peak in the spectrum, not every bin above
    threshold (a strong signal spans many adjacent bins, but should
    only count as one peak)."""
    threshold_db = estimate_noise_floor_db(magnitude_db) + margin_db
    peaks: set[int] = set()
    for i in range(1, len(magnitude_db) - 1):
        value = magnitude_db[i]
        if value < threshold_db:
            continue
        if value >= magnitude_db[i - 1] and value >= magnitude_db[i + 1]:
            peaks.add(i)
    return peaks


def bin_to_frequency_offset_hz(bin_index: int, fft_size: int, sample_rate_hz: int) -> float:
    """Frequency offset from the tuned center for a bin in an
    fftshift'd magnitude array (bin `fft_size // 2` is the center)."""
    return (bin_index - fft_size / 2) * sample_rate_hz / fft_size


class PeakTracker:
    """Decides which detected peaks are worth emitting an event for.

    A first attempt at this used a tight per-frame bin-tolerance check
    (was this peak within N bins of one seen last frame?) -- verified
    against a real FM broadcast carrier, it was nowhere near enough: a
    real signal's peak bin wanders by far more than a couple of bins
    frame-to-frame (modulation, noise, frequency drift), so that
    approach re-"detected" the same carrier dozens of times per second.
    Grouping bins into coarser buckets and cooling down each bucket for
    a few seconds after it triggers is what real scanner/signal-detect
    software does, and is what actually produces one notification per
    signal appearance instead of a flood.
    """

    def __init__(self, bucket_width_bins: int = 8, cooldown_seconds: float = 5.0) -> None:
        self._bucket_width_bins = bucket_width_bins
        self._cooldown_seconds = cooldown_seconds
        self._last_triggered_at: dict[int, float] = {}

    def filter_new(self, current_bins: set[int], now: float) -> set[int]:
        new_bins = set()
        for bin_index in current_bins:
            bucket = bin_index // self._bucket_width_bins
            last_triggered_at = self._last_triggered_at.get(bucket)
            if last_triggered_at is None or (now - last_triggered_at) >= self._cooldown_seconds:
                new_bins.add(bin_index)
                self._last_triggered_at[bucket] = now
        return new_bins
