""""Record when a signal is detected" (Phase 8: triggered recording).

Reuses two things that already exist rather than inventing new
plumbing: `SignalDetected` events (already emitted by
`_ReceiverCapture._detect_signals`, already require the user to enable
signal detection with a `margin_db` first) as the trigger source, and
`RecordingService.start`/`stop` as the recording mechanism. This
service is just the glue between them -- a receiver_id -> config map
("arm" state) plus a single `EventBus` subscriber that starts a
fixed-duration recording the first time a detection comes in for an
armed receiver that isn't already recording, and auto-stops it after
`duration_seconds`.

Deliberately doesn't re-arm/extend an in-progress triggered recording
on additional detections during its window -- a burst of detections
(the common case: one real signal crossing several FFT frames) would
otherwise never let the recording stop. One recording per trigger,
capped at `duration_seconds`, is the simple version; a real
retrigger/extend policy is a bigger feature for actual field use.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.core.events import Event
from app.services.receiver_service import ReceiverService
from app.services.recording_service import RecordingAlreadyActiveError, RecordingService

logger = logging.getLogger("echo_base.triggered_recording")


@dataclass
class _ArmedConfig:
    mode: str
    duration_seconds: float


class TriggeredRecordingService:
    def __init__(self, recording_service: RecordingService, receiver_service: ReceiverService) -> None:
        self._recording_service = recording_service
        self._receiver_service = receiver_service
        self._armed: dict[str, _ArmedConfig] = {}
        self._stop_tasks: dict[str, asyncio.Task] = {}

    def enable(self, receiver_id: str, mode: str, duration_seconds: float) -> None:
        self._armed[receiver_id] = _ArmedConfig(mode, duration_seconds)

    def disable(self, receiver_id: str) -> None:
        self._armed.pop(receiver_id, None)
        task = self._stop_tasks.pop(receiver_id, None)
        if task is not None:
            task.cancel()

    def is_armed(self, receiver_id: str) -> bool:
        return receiver_id in self._armed

    async def handle_signal_detected(self, event: Event) -> None:
        config = self._armed.get(event.source)
        if config is None:
            return
        if self._recording_service.is_recording(event.source):
            return  # already recording (manually, or from an earlier trigger still running)

        status = await self._receiver_service.status(event.source)
        try:
            await self._recording_service.start(event.source, config.mode, status.frequency_hz)
        except RecordingAlreadyActiveError:
            return  # lost a race with a manual start between the check above and now
        logger.info(
            "Triggered recording started for '%s' (mode=%s, %ss)",
            event.source,
            config.mode,
            config.duration_seconds,
        )
        self._stop_tasks[event.source] = asyncio.create_task(
            self._auto_stop(event.source, config.duration_seconds)
        )

    async def _auto_stop(self, receiver_id: str, duration_seconds: float) -> None:
        try:
            await asyncio.sleep(duration_seconds)
            await self._recording_service.stop(receiver_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to auto-stop triggered recording for '%s'", receiver_id)
        finally:
            self._stop_tasks.pop(receiver_id, None)

    def shutdown(self) -> None:
        for task in self._stop_tasks.values():
            task.cancel()
