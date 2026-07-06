import numpy as np

from app.services.signal_detection import (
    OccupancyTracker,
    PeakTracker,
    bin_to_frequency_offset_hz,
    find_peak_bins,
)


def _synthetic_spectrum(peak_bins: dict[int, float], size: int = 64, floor_db: float = -80.0) -> np.ndarray:
    spectrum = np.full(size, floor_db, dtype=np.float32)
    for bin_index, power in peak_bins.items():
        spectrum[bin_index] = power
    return spectrum


def test_finds_single_isolated_peak():
    spectrum = _synthetic_spectrum({32: -10.0})
    assert find_peak_bins(spectrum, margin_db=30.0) == {32}


def test_ignores_peaks_below_margin_above_noise_floor():
    spectrum = _synthetic_spectrum({32: -60.0})  # only 20dB above the -80dB floor
    assert find_peak_bins(spectrum, margin_db=25.0) == set()


def test_finds_multiple_separated_peaks():
    spectrum = _synthetic_spectrum({10: -5.0, 50: -15.0})
    assert find_peak_bins(spectrum, margin_db=30.0) == {10, 50}


def test_wide_signal_counts_as_one_peak_not_many_bins():
    spectrum = _synthetic_spectrum({}, floor_db=-80.0)
    # A signal spanning several bins with one true maximum, e.g. a
    # slightly-off-rectangular pulse -- only the actual local max
    # should register, not every bin that happens to be >= threshold.
    spectrum[20:26] = [-20.0, -15.0, -10.0, -12.0, -18.0, -25.0]
    assert find_peak_bins(spectrum, margin_db=30.0) == {22}


def test_threshold_adapts_to_noise_floor_not_absolute_scale():
    """The same margin_db catches a peak regardless of what absolute dB
    scale the spectrum happens to sit at (e.g. different receiver gain)
    -- this is the actual bug found live against real hardware: a fixed
    *absolute* threshold worked at one gain setting and completely
    misbehaved (either catching nothing or nearly everything) at another."""
    low_gain_spectrum = _synthetic_spectrum({32: -40.0}, floor_db=-60.0)
    high_gain_spectrum = _synthetic_spectrum({32: 10.0}, floor_db=-10.0)
    assert find_peak_bins(low_gain_spectrum, margin_db=15.0) == {32}
    assert find_peak_bins(high_gain_spectrum, margin_db=15.0) == {32}


def test_bin_to_frequency_offset_center_bin_is_zero():
    assert bin_to_frequency_offset_hz(bin_index=32, fft_size=64, sample_rate_hz=240_000) == 0


def test_bin_to_frequency_offset_scales_with_sample_rate():
    offset = bin_to_frequency_offset_hz(bin_index=48, fft_size=64, sample_rate_hz=240_000)
    assert offset == (48 - 32) * 240_000 / 64


def test_peak_tracker_suppresses_repeat_within_cooldown():
    tracker = PeakTracker(bucket_width_bins=8, cooldown_seconds=5.0)
    assert tracker.filter_new({50}, now=0.0) == {50}
    # Same signal, drifted well beyond any small bin-tolerance window
    # (as a real FM broadcast carrier does frame-to-frame) but still
    # the same bucket, well within the cooldown window.
    assert tracker.filter_new({55}, now=1.0) == set()
    assert tracker.filter_new({50}, now=4.9) == set()


def test_peak_tracker_allows_repeat_after_cooldown_elapses():
    tracker = PeakTracker(bucket_width_bins=8, cooldown_seconds=5.0)
    assert tracker.filter_new({50}, now=0.0) == {50}
    assert tracker.filter_new({50}, now=5.1) == {50}


def test_peak_tracker_treats_different_buckets_independently():
    tracker = PeakTracker(bucket_width_bins=8, cooldown_seconds=5.0)
    assert tracker.filter_new({10}, now=0.0) == {10}
    assert tracker.filter_new({10, 50}, now=1.0) == {50}  # 10 still cooling down, 50 is new


def test_occupancy_tracker_starts_at_zero():
    tracker = OccupancyTracker(num_bins=64, decay=0.9)
    assert (tracker.occupancy_percent() == 0).all()


def test_occupancy_tracker_converges_toward_100_for_always_occupied_bin():
    tracker = OccupancyTracker(num_bins=64, decay=0.9)
    spectrum = _synthetic_spectrum({32: -10.0})  # bin 32 always well above the floor
    for _ in range(200):
        tracker.record_frame(spectrum, margin_db=30.0)
    occupancy = tracker.occupancy_percent()
    assert occupancy[32] > 99.0
    assert occupancy[0] < 1.0  # never-occupied bins stay near zero


def test_occupancy_tracker_decays_when_signal_disappears():
    tracker = OccupancyTracker(num_bins=64, decay=0.9)
    occupied = _synthetic_spectrum({32: -10.0})
    quiet = _synthetic_spectrum({})
    for _ in range(100):
        tracker.record_frame(occupied, margin_db=30.0)
    high_water_mark = tracker.occupancy_percent()[32]
    for _ in range(100):
        tracker.record_frame(quiet, margin_db=30.0)
    assert tracker.occupancy_percent()[32] < high_water_mark
    assert tracker.occupancy_percent()[32] < 1.0
