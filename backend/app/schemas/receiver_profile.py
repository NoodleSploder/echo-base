from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReceiverProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    frequency_hz: int = Field(gt=0)
    sample_rate_hz: int | None = Field(default=None, gt=0)
    bandwidth_hz: int | None = Field(default=None, gt=0)
    gain: str | None = None
    decoder: str | None = None


class ReceiverProfileUpdate(ReceiverProfileCreate):
    pass


class ReceiverProfileSchema(BaseModel):
    id: str
    name: str
    frequency_hz: int
    sample_rate_hz: int | None
    bandwidth_hz: int | None
    gain: str | None
    decoder: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
