"""Receiver plugin contract and shared data types.

A single plugin instance represents an entire hardware driver (e.g.
"rtl_sdr") and may therefore manage more than one physical device --
this is why the lifecycle methods take an explicit ``receiver_id``
rather than assuming one device per plugin instance, refining the
draft interface in docs/PLUGIN_API.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.plugins.base import Plugin


@dataclass
class ReceiverDescriptor:
    """Describes a single physical (or virtual) receiver a plugin can control."""

    id: str
    name: str
    driver: str
    serial: str | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReceiverStatus:
    """Current operational state of a receiver."""

    id: str
    state: str  # "idle" | "streaming" | "error" | "disconnected"
    frequency_hz: int | None = None
    sample_rate_hz: int | None = None
    bandwidth_hz: int | None = None
    gain: str | float | None = None
    detail: str | None = None


class IqStreamHandle(Protocol):
    """A running raw-IQ capture a plugin has started for one receiver.

    Samples are interleaved unsigned 8-bit I/Q pairs (the format
    `rtl_sdr` and most similar command-line SDR tools emit), read in
    blocking chunks by ``SpectrumService`` from a background thread --
    never from the asyncio event loop.
    """

    sample_rate_hz: int

    def read(self, n: int) -> bytes:
        """Block until at least some bytes are available; return b"" on EOF."""
        ...

    def close(self) -> None: ...


class ReceiverPlugin(Plugin):
    """Base class for plugins that expose SDR/receiver hardware."""

    def discover(self) -> list[ReceiverDescriptor]:
        """Return the receivers currently visible to this plugin."""
        return []

    def start(self, receiver_id: str) -> ReceiverStatus:
        raise NotImplementedError

    def stop(self, receiver_id: str) -> ReceiverStatus:
        raise NotImplementedError

    def tune(self, receiver_id: str, frequency_hz: int) -> ReceiverStatus:
        raise NotImplementedError

    def set_gain(self, receiver_id: str, gain: str | float) -> ReceiverStatus:
        raise NotImplementedError

    def set_bandwidth(self, receiver_id: str, bandwidth_hz: int) -> ReceiverStatus:
        raise NotImplementedError

    def set_sample_rate(self, receiver_id: str, sample_rate_hz: int) -> ReceiverStatus:
        raise NotImplementedError

    def device_status(self, receiver_id: str) -> ReceiverStatus:
        """Per-device status. Distinct from the inherited `Plugin.status()`,
        which reports plugin-level (not per-device) health."""
        raise NotImplementedError

    def open_iq_stream(self, receiver_id: str) -> IqStreamHandle:
        """Start a raw-IQ capture for live spectrum display.

        Optional: plugins that can't stream raw samples (or haven't
        implemented it yet) should leave this raising
        NotImplementedError, which SpectrumService treats as "no live
        spectrum available for this receiver" rather than an error.
        """
        raise NotImplementedError
