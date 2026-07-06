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
    detail: str | None = None


class TuneRequest(BaseModel):
    frequency: int


class GainRequest(BaseModel):
    gain: str | float


class BandwidthRequest(BaseModel):
    bandwidth: int


class SampleRateRequest(BaseModel):
    sample_rate: int
