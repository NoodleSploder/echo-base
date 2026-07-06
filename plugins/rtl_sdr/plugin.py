"""RTL-SDR receiver plugin.

Discovers RTL-SDR dongles via the `rtl_test` command-line tool (part of
the rtl-sdr project) and models basic lifecycle/tuning state. Actual IQ
sample streaming is not implemented yet -- see ROADMAP.md Phase 2/4 --
so `start()` only marks a device as claimed/streaming for the purposes
of the dashboard and future decoder wiring.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from app.plugins import PluginContext, ReceiverDescriptor, ReceiverPlugin, ReceiverStatus


@dataclass
class _DeviceState:
    descriptor: ReceiverDescriptor
    state: str = "idle"
    frequency_hz: int | None = None
    sample_rate_hz: int | None = 2_048_000
    bandwidth_hz: int | None = None
    gain: str | float = "auto"


class RtlSdrReceiverPlugin(ReceiverPlugin):
    """Receiver plugin backed by the rtl-sdr command-line tools."""

    def __init__(self, context: PluginContext) -> None:
        super().__init__(context)
        self._devices: dict[str, _DeviceState] = {}

    def initialize(self) -> None:
        self.logger.info("RTL-SDR plugin initialized.")

    def discover(self) -> list[ReceiverDescriptor]:
        binary = shutil.which("rtl_test")
        if binary is None:
            self.logger.warning("rtl_test not found on PATH; install rtl-sdr to enable RTL-SDR support.")
            return []

        try:
            result = subprocess.run(
                [binary, "-t"],
                capture_output=True,
                text=True,
                timeout=self.config.get("discovery_timeout_seconds", 5),
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            self.logger.warning("RTL-SDR discovery failed: %s", exc)
            return []

        descriptors = self._parse_devices(f"{result.stdout}\n{result.stderr}")

        # Preserve live state for devices that are still present; drop the rest.
        self._devices = {d.id: self._devices.get(d.id, _DeviceState(descriptor=d)) for d in descriptors}
        return descriptors

    @staticmethod
    def _parse_devices(output: str) -> list[ReceiverDescriptor]:
        if "No supported devices found" in output:
            return []

        descriptors: list[ReceiverDescriptor] = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            index_part, _, remainder = line.partition(":")
            if not index_part.isdigit():
                continue

            remainder = remainder.strip()
            if ", SN:" in remainder:
                description, _, serial_part = remainder.partition(", SN:")
                serial = serial_part.strip() or None
            else:
                description, serial = remainder, None

            descriptors.append(
                ReceiverDescriptor(
                    id=f"rtl_sdr:{serial or index_part}",
                    name=description.strip(),
                    driver="rtl_sdr",
                    serial=serial,
                    capabilities={"tunable": True, "iq_streaming": False},
                )
            )
        return descriptors

    def _require(self, receiver_id: str) -> _DeviceState:
        try:
            return self._devices[receiver_id]
        except KeyError:
            raise RuntimeError(f"Unknown RTL-SDR receiver '{receiver_id}'") from None

    def start(self, receiver_id: str) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.state = "streaming"
        self.logger.info("Started receiver '%s'.", receiver_id)
        return self.device_status(receiver_id)

    def stop(self, receiver_id: str) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.state = "idle"
        self.logger.info("Stopped receiver '%s'.", receiver_id)
        return self.device_status(receiver_id)

    def tune(self, receiver_id: str, frequency_hz: int) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.frequency_hz = frequency_hz
        return self.device_status(receiver_id)

    def set_gain(self, receiver_id: str, gain: str | float) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.gain = gain
        return self.device_status(receiver_id)

    def set_bandwidth(self, receiver_id: str, bandwidth_hz: int) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.bandwidth_hz = bandwidth_hz
        return self.device_status(receiver_id)

    def set_sample_rate(self, receiver_id: str, sample_rate_hz: int) -> ReceiverStatus:
        device = self._require(receiver_id)
        device.sample_rate_hz = sample_rate_hz
        return self.device_status(receiver_id)

    def device_status(self, receiver_id: str) -> ReceiverStatus:
        device = self._require(receiver_id)
        return ReceiverStatus(
            id=receiver_id,
            state=device.state,
            frequency_hz=device.frequency_hz,
            sample_rate_hz=device.sample_rate_hz,
            bandwidth_hz=device.bandwidth_hz,
            gain=device.gain,
            detail=None,
        )
