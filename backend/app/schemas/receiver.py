from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ReceiverDescriptorSchema(BaseModel):
    id: str
    name: str
    driver: str
    serial: str | None = None
    capabilities: dict[str, Any] = {}


class ReceiverStatusSchema(BaseModel):
    id: str
    state: str
    frequency_hz: int | None = None
    sample_rate_hz: int | None = None
    bandwidth_hz: int | None = None
    gain: str | float | None = None
    ppm_correction: int | None = None
    detail: str | None = None


class TuneRequest(BaseModel):
    frequency: int


class GainRequest(BaseModel):
    gain: str | float


class BandwidthRequest(BaseModel):
    bandwidth: int


class SampleRateRequest(BaseModel):
    sample_rate: int


class PpmCorrectionRequest(BaseModel):
    ppm: int


class SignalDetectionRequest(BaseModel):
    # dB above the spectrum's own estimated noise floor, not an absolute
    # value -- the raw FFT scale isn't calibrated and shifts with gain
    # (see signal_detection.py's docstring).
    margin_db: float = 15.0


class ScanRequest(BaseModel):
    frequencies: list[int]
    dwell_seconds: float = 2.0
