"""Records a receiver's demodulated audio (WAV) or raw IQ samples to disk.

A recording is just another consumer of an existing `StreamService`
subscriber queue (the same one `/ws/audio` uses for demodulated audio,
or the raw-IQ one spectrum recording could use) -- an asyncio task
pulls chunks off the queue and writes them straight into a file
instead of a WebSocket. No new capture/hardware-claim path, reusing
the one established by spectrum/audio/APRS/SAME.

Recording metadata (receiver, mode, frequency at record time) is
encoded in the filename rather than a database table, since it's
exactly the same "small enough not to need real persistence, and
derivable from what's already on disk" situation `ReceiverProfile` is
not -- profiles are user data meant to survive and be edited;
recordings are immutable files. `receiver_id` is sanitized for the
filename (it may contain `:`), so the *authoritative* receiver_id for
a currently-active recording is whatever's tracked in `_active`, not
whatever gets reconstructed by re-parsing the (lossy) filename --
that reconstruction is only used for recordings from past runs that
aren't in `_active` anymore.

Audio recordings are `.wav` (self-describing: sample rate lives in the
WAV header). Raw IQ recordings are `.iq` (interleaved uint8 I/Q pairs,
the same format `rtl_sdr`'s own file output uses, directly usable by
GNU Radio/inspectrum/etc.) with a `.iq.json` sidecar holding the
sample rate, since a raw binary file has no header of its own to carry
that in.
"""
from __future__ import annotations

import asyncio
import json
import re
import wave
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.exceptions import ConflictError, NotFoundError
from app.services.dsp import AUDIO_SAMPLE_RATE_HZ
from app.services.stream_service import StreamService

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]")
IQ_MODE = "iq"


class RecordingAlreadyActiveError(ConflictError):
    code = "RECORDING_ALREADY_ACTIVE"


class RecordingNotFoundError(NotFoundError):
    code = "RECORDING_NOT_FOUND"


def _safe_component(value: str) -> str:
    return _UNSAFE_FILENAME_CHARS.sub("_", value)


@dataclass
class RecordingInfo:
    filename: str
    receiver_id: str
    mode: str
    frequency_hz: int | None
    started_at: str
    duration_seconds: float
    size_bytes: int
    active: bool


class _ActiveRecording:
    def __init__(
        self,
        receiver_id: str,
        mode: str,
        frequency_hz: int | None,
        started_at: datetime,
        path: Path,
        queue: asyncio.Queue[bytes],
        task: asyncio.Task,
    ) -> None:
        self.receiver_id = receiver_id
        self.mode = mode
        self.frequency_hz = frequency_hz
        self.started_at = started_at
        self.path = path
        self.queue = queue
        self.task = task


def _sidecar_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".json")


class RecordingService:
    def __init__(self, stream_service: StreamService, recordings_dir: Path) -> None:
        self._stream_service = stream_service
        self._recordings_dir = recordings_dir
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, _ActiveRecording] = {}

    async def start(self, receiver_id: str, mode: str, frequency_hz: int | None) -> RecordingInfo:
        if receiver_id in self._active:
            raise RecordingAlreadyActiveError(f"Receiver '{receiver_id}' is already recording.")

        is_iq = mode == IQ_MODE
        queue = (
            await self._stream_service.subscribe_iq(receiver_id)
            if is_iq
            else await self._stream_service.subscribe_audio(receiver_id, mode)
        )

        started_at = datetime.now(UTC)
        freq_component = str(frequency_hz) if frequency_hz is not None else "unknown"
        extension = "iq" if is_iq else "wav"
        filename = (
            f"{_safe_component(receiver_id)}_{mode}_{freq_component}_"
            f"{started_at.strftime('%Y%m%dT%H%M%SZ')}.{extension}"
        )
        path = self._recordings_dir / filename

        if is_iq:
            sample_rate_hz = self._stream_service.get_sample_rate(receiver_id) or AUDIO_SAMPLE_RATE_HZ
            _sidecar_path(path).write_text(json.dumps({"sample_rate_hz": sample_rate_hz}))
            raw_file = path.open("wb")
            task = asyncio.create_task(self._write_raw_loop(queue, raw_file))
        else:
            wav_file = wave.open(str(path), "wb")
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(AUDIO_SAMPLE_RATE_HZ)
            task = asyncio.create_task(self._write_wav_loop(queue, wav_file))

        self._active[receiver_id] = _ActiveRecording(
            receiver_id, mode, frequency_hz, started_at, path, queue, task
        )

        return RecordingInfo(
            filename=filename,
            receiver_id=receiver_id,
            mode=mode,
            frequency_hz=frequency_hz,
            started_at=started_at.isoformat(),
            duration_seconds=0.0,
            size_bytes=0,
            active=True,
        )

    async def stop(self, receiver_id: str) -> RecordingInfo:
        active = self._active.pop(receiver_id, None)
        if active is None:
            raise RecordingNotFoundError(f"Receiver '{receiver_id}' is not currently recording.")

        active.task.cancel()
        try:
            await active.task
        except asyncio.CancelledError:
            pass

        if active.mode == IQ_MODE:
            await self._stream_service.unsubscribe_iq(receiver_id, active.queue)
        else:
            await self._stream_service.unsubscribe_audio(receiver_id, active.mode, active.queue)

        return self._describe_file(
            active.path, active=False, receiver_id=active.receiver_id, mode=active.mode
        )

    @staticmethod
    async def _write_wav_loop(queue: asyncio.Queue[bytes], wav_file: wave.Wave_write) -> None:
        try:
            while True:
                chunk = await queue.get()
                wav_file.writeframes(chunk)
        finally:
            wav_file.close()

    @staticmethod
    async def _write_raw_loop(queue: asyncio.Queue[bytes], raw_file) -> None:
        try:
            while True:
                chunk = await queue.get()
                raw_file.write(chunk)
        finally:
            raw_file.close()

    def is_recording(self, receiver_id: str) -> bool:
        return receiver_id in self._active

    def _describe_file(
        self, path: Path, active: bool, receiver_id: str | None = None, mode: str | None = None
    ) -> RecordingInfo:
        # Filename shape: "{receiver_id}_{mode}_{freq}_{timestamp}.{wav|iq}".
        # receiver_id/mode are reconstructed from it only as a fallback for
        # recordings from past runs no longer in `_active` -- lossy for
        # receiver_ids containing sanitized characters (":" -> "_"), which
        # is why an active recording's *tracked* values always take
        # precedence when available.
        parts = path.stem.split("_")
        raw_timestamp, freq_component = parts[-1], parts[-2]
        receiver_id = receiver_id if receiver_id is not None else "_".join(parts[:-3])
        mode = mode if mode is not None else parts[-3]
        frequency_hz = int(freq_component) if freq_component.isdigit() else None

        # Match start()'s ISO-formatted `started_at` rather than leaking
        # the filename's compact "%Y%m%dT%H%M%SZ" form to API consumers.
        try:
            timestamp = datetime.strptime(raw_timestamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC).isoformat()
        except ValueError:
            timestamp = raw_timestamp

        size_bytes = path.stat().st_size
        if path.suffix == ".iq":
            try:
                sidecar = json.loads(_sidecar_path(path).read_text())
                sample_rate_hz = sidecar["sample_rate_hz"]
            except (OSError, json.JSONDecodeError, KeyError):
                sample_rate_hz = AUDIO_SAMPLE_RATE_HZ
            duration = size_bytes / 2 / sample_rate_hz  # 2 bytes per I/Q sample pair
        else:
            with wave.open(str(path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate() or AUDIO_SAMPLE_RATE_HZ
                duration = frames / rate

        return RecordingInfo(
            filename=path.name,
            receiver_id=receiver_id,
            mode=mode,
            frequency_hz=frequency_hz,
            started_at=timestamp,
            duration_seconds=round(duration, 2),
            size_bytes=size_bytes,
            active=active,
        )

    def list_recordings(self) -> list[RecordingInfo]:
        active_by_path = {active.path: active for active in self._active.values()}
        recordings = []
        paths = sorted(
            (*self._recordings_dir.glob("*.wav"), *self._recordings_dir.glob("*.iq")),
            reverse=True,
        )
        for path in paths:
            active = active_by_path.get(path)
            try:
                recordings.append(
                    self._describe_file(
                        path,
                        active=active is not None,
                        receiver_id=active.receiver_id if active else None,
                        mode=active.mode if active else None,
                    )
                )
            except (wave.Error, OSError):
                continue  # a recording still being written may briefly have no valid header
        return recordings

    def path_for(self, filename: str) -> Path:
        path = self._recordings_dir / filename
        if not path.is_file() or path.resolve().parent != self._recordings_dir.resolve():
            raise RecordingNotFoundError(f"Recording '{filename}' not found.")
        return path

    def sample_rate_for(self, filename: str) -> int:
        """The IQ sample rate of a `.iq` recording, for playback. Raises
        RecordingNotFoundError if the file (or its sidecar) is missing."""
        path = self.path_for(filename)
        try:
            sidecar = json.loads(_sidecar_path(path).read_text())
            return sidecar["sample_rate_hz"]
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise RecordingNotFoundError(f"No sample rate metadata for '{filename}'.") from exc

    def delete(self, filename: str) -> None:
        path = self.path_for(filename)
        if any(active.path == path for active in self._active.values()):
            raise RecordingAlreadyActiveError(f"Recording '{filename}' is still recording; stop it first.")
        path.unlink()
        _sidecar_path(path).unlink(missing_ok=True)

    def shutdown(self) -> None:
        for active in self._active.values():
            active.task.cancel()
