"""dsp.py demodulators: usb_discriminator/usb_demodulate specifically
(added for FT8, which needs real SSB audio, not FM/AM) -- a real tone
in the complex baseband's real part should come out the other end as
that same tone, decimated to audio rate.
"""
from __future__ import annotations

import numpy as np

from app.services.dsp import usb_demodulate, usb_discriminator

SAMPLE_RATE_HZ = 48_000


def test_usb_discriminator_recovers_a_real_tone():
    tone_hz = 800.0
    duration_s = 0.05
    t = np.arange(int(duration_s * SAMPLE_RATE_HZ)) / SAMPLE_RATE_HZ
    # A real SSB baseband signal: the real part carries the audio tone,
    # the imaginary part is whatever the (irrelevant, for USB demod)
    # quadrature component happens to be -- usb_discriminator should
    # only ever look at the real part.
    iq = np.cos(2 * np.pi * tone_hz * t) + 1j * np.sin(2 * np.pi * tone_hz * t) * 5

    audio = usb_discriminator(iq, decimation=1)
    assert len(audio) == len(iq)
    np.testing.assert_allclose(audio, np.cos(2 * np.pi * tone_hz * t), atol=1e-5)


def test_usb_discriminator_decimates():
    iq = np.ones(100, dtype=np.complex64)
    audio = usb_discriminator(iq, decimation=10)
    assert len(audio) == 10


def test_usb_discriminator_empty_input():
    assert len(usb_discriminator(np.zeros(0, dtype=np.complex64), decimation=1)) == 0


def test_usb_demodulate_returns_pcm16_bytes():
    t = np.arange(4800) / SAMPLE_RATE_HZ
    iq = (np.cos(2 * np.pi * 440 * t) + 1j * np.zeros_like(t)).astype(np.complex64)
    pcm = usb_demodulate(iq, decimation=1)
    assert isinstance(pcm, bytes)
    assert len(pcm) == len(iq) * 2  # int16 = 2 bytes/sample
