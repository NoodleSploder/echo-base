"""RTL-SDR receiver plugin.

Discovers RTL-SDR dongles via the `rtl_test` command-line tool (part of
the rtl-sdr project) and models basic lifecycle/tuning state. Raw IQ
streaming (for live spectrum display) shells out to `rtl_sdr` the same
way discovery shells out to `rtl_test` -- see `open_iq_stream` below.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from app.plugins import IqStreamHandle, PluginContext, ReceiverDescriptor, ReceiverPlugin, ReceiverStatus


@dataclass
class _DeviceState:
    descriptor: ReceiverDescriptor
    index: int
    state: str = "idle"
    frequency_hz: int | None = None
    sample_rate_hz: int | None = 2_048_000
    bandwidth_hz: int | None = None
    gain: str | float = "auto"


class _RtlSdrIqStream:
    """Wraps a running `rtl_sdr ... -` subprocess emitting raw uint8 I/Q pairs on stdout."""

    def __init__(self, process: subprocess.Popen, sample_rate_hz: int) -> None:
        self._process = process
        self.sample_rate_hz = sample_rate_hz

    def read(self, n: int) -> bytes:
        assert self._process.stdout is not None
        return self._process.stdout.read(n)

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()


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

        parsed = self._parse_devices(f"{result.stdout}\n{result.stderr}")

        # Preserve live state for devices that are still present; drop the rest.
        self._devices = {
            descriptor.id: self._devices.get(descriptor.id, _DeviceState(descriptor=descriptor, index=index))
            for descriptor, index in parsed
        }
        return [descriptor for descriptor, _ in parsed]

    @staticmethod
    def _parse_devices(output: str) -> list[tuple[ReceiverDescriptor, int]]:
        if "No supported devices found" in output:
            return []

        parsed: list[tuple[ReceiverDescriptor, int]] = []
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

            descriptor = ReceiverDescriptor(
                id=f"rtl_sdr:{serial or index_part}",
                name=description.strip(),
                driver="rtl_sdr",
                serial=serial,
                capabilities={"tunable": True, "iq_streaming": True},
            )
            parsed.append((descriptor, int(index_part)))
        return parsed

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

    def open_iq_stream(self, receiver_id: str) -> IqStreamHandle:
        device = self._require(receiver_id)
        binary = shutil.which("rtl_sdr")
        if binary is None:
            raise RuntimeError("rtl_sdr binary not found on PATH; install rtl-sdr to enable live spectrum.")

        # Untuned receivers still get a usable spectrum preview rather
        # than requiring the user to tune before a waterfall appears.
        frequency_hz = device.frequency_hz or 100_000_000
        sample_rate_hz = device.sample_rate_hz or 2_048_000

        args = [binary, "-d", str(device.index), "-f", str(frequency_hz), "-s", str(sample_rate_hz)]
        if isinstance(device.gain, int | float) or (isinstance(device.gain, str) and device.gain != "auto"):
            args += ["-g", str(device.gain)]
        args.append("-")  # write raw samples to stdout

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.logger.info(
            "Opened IQ stream for '%s' (%s Hz @ %s S/s).", receiver_id, frequency_hz, sample_rate_hz
        )
        return _RtlSdrIqStream(process, sample_rate_hz)
