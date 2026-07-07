"""Software demodulators applied to raw IQ, shared by StreamService.

Kept separate from stream_service.py so the DSP math (easy to get
subtly wrong) can be read and unit-tested in isolation from the
threading/subscriber plumbing around it.
"""
from __future__ import annotations

import numpy as np

AUDIO_SAMPLE_RATE_HZ = 48_000
AGC_TARGET_PEAK = 0.8 * 32767


def _decimate_mean(values: np.ndarray, factor: int) -> np.ndarray:
    """Crude boxcar low-pass + downsample: averages every `factor` consecutive
    samples. Not a sharp filter, but enough to keep voice-grade demod
    intelligible without pulling in scipy for a proper FIR/IIR filter."""
    usable = (len(values) // factor) * factor
    if usable == 0:
        return values[:0]
    return values[:usable].reshape(-1, factor).mean(axis=1)


def _to_pcm16(samples: np.ndarray) -> bytes:
    """Per-chunk AGC: normalizes to a fixed target peak so volume stays
    roughly constant regardless of signal strength, then clips to int16."""
    peak = np.max(np.abs(samples)) if samples.size else 0.0
    if peak > 1e-9:
        samples = samples * (AGC_TARGET_PEAK / peak)
    return np.clip(samples, -32768, 32767).astype(np.int16).tobytes()


def fm_discriminator(iq: np.ndarray, decimation: int) -> np.ndarray:
    """Narrowband FM discriminator: instantaneous frequency (phase difference
    between consecutive samples), decimated to audio rate. Raw float
    output, not yet AGC'd/quantized -- shared by `fm_demodulate` (for
    playback) and AFSK1200 decoding (`decoders.afsk`), which needs the
    actual waveform rather than a volume-normalized copy of it."""
    if len(iq) < 2:
        return np.zeros(0, dtype=np.float32)
    phase_diff = np.angle(iq[1:] * np.conj(iq[:-1]))
    return _decimate_mean(phase_diff, decimation)


def fm_demodulate(iq: np.ndarray, decimation: int) -> bytes:
    """Narrowband FM, AGC'd and quantized to PCM16 for playback."""
    return _to_pcm16(fm_discriminator(iq, decimation))


def am_demodulate(iq: np.ndarray, decimation: int) -> bytes:
    """AM: envelope (magnitude) demod, DC-blocked, then decimated."""
    if len(iq) == 0:
        return b""
    envelope = np.abs(iq)
    envelope = envelope - envelope.mean()
    decimated = _decimate_mean(envelope, decimation)
    return _to_pcm16(decimated)


def usb_discriminator(iq: np.ndarray, decimation: int) -> np.ndarray:
    """Upper-sideband SSB demod (needed for FT8, which is virtually
    always transmitted USB on HF): taking the real part of the complex
    baseband directly recovers the audio, *provided* the receiver is
    tuned to the conventional USB dial frequency (the suppressed-
    carrier point, with the voice/tone passband sitting entirely above
    it in baseband) -- the same simple technique general-purpose SDR
    software (GQRX, SDR#) uses for SSB; no Hilbert-transform sideband-
    selecting filter is needed when that tuning convention is
    followed. Raw float output, not yet AGC'd/quantized -- shared by
    `usb_demodulate` (for playback) and FT8 decoding."""
    if len(iq) == 0:
        return np.zeros(0, dtype=np.float32)
    return _decimate_mean(np.real(iq), decimation)


def usb_demodulate(iq: np.ndarray, decimation: int) -> bytes:
    """Upper sideband (USB), AGC'd and quantized to PCM16 for playback."""
    return _to_pcm16(usb_discriminator(iq, decimation))


DEMODULATORS = {
    "fm": fm_demodulate,
    "am": am_demodulate,
    "usb": usb_demodulate,
}
