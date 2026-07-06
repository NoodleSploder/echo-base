"""Start/stop a recording at a wall-clock time (Phase 8: scheduled
recording).

Same "reuse `RecordingService.start`/`stop`, add only the glue" shape
as `triggered_recording.py` -- here the trigger is a timer instead of
a `SignalDetected` event. In-memory only (like triggered recording's
armed state): a scheduled job is lost if the backend restarts before
it fires. That's an acceptable gap for a first version -- worth
persisting properly (a DB row + a startup reconciliation pass) if this
becomes something people rely on across restarts, but not a blocker
for "schedule a recording 10 minutes from now and walk away."
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.exceptions import ValidationAppError
from app.services.receiver_service import ReceiverService
from app.services.recording_service import RecordingAlreadyActiveError, RecordingService

logger = logging.getLogger("echo_base.scheduled_recording")


@dataclass
class ScheduledJob:
    id: str
    receiver_id: str
    mode: str
    start_at: datetime
    duration_seconds: float
    status: str  # "pending" | "recording" | "done" | "failed" | "cancelled"


class ScheduledRecordingService:
    def __init__(self, recording_service: RecordingService, receiver_service: ReceiverService) -> None:
        self._recording_service = recording_service
        self._receiver_service = receiver_service
        self._jobs: dict[str, ScheduledJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def schedule(
        self, receiver_id: str, mode: str, start_at: datetime, duration_seconds: float
    ) -> ScheduledJob:
        if duration_seconds <= 0:
            raise ValidationAppError("duration_seconds must be positive.")
        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=UTC)

        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            id=job_id,
            receiver_id=receiver_id,
            mode=mode,
            start_at=start_at,
            duration_seconds=duration_seconds,
            status="pending",
        )
        self._jobs[job_id] = job
        self._tasks[job_id] = asyncio.create_task(self._run(job_id))
        return job

    def cancel(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.status = "cancelled"
        task = self._tasks.pop(job_id, None)
        if task is not None:
            task.cancel()

    def list_jobs(self, receiver_id: str | None = None) -> list[ScheduledJob]:
        jobs = list(self._jobs.values())
        if receiver_id is not None:
            jobs = [j for j in jobs if j.receiver_id == receiver_id]
        return sorted(jobs, key=lambda j: j.start_at)

    async def _run(self, job_id: str) -> None:
        job = self._jobs[job_id]
        delay = (job.start_at - datetime.now(UTC)).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

        started = False
        try:
            status = await self._receiver_service.status(job.receiver_id)
            await self._recording_service.start(job.receiver_id, job.mode, status.frequency_hz)
            started = True
            job.status = "recording"
            logger.info("Scheduled recording started for '%s' (mode=%s)", job.receiver_id, job.mode)
            await asyncio.sleep(job.duration_seconds)
            await self._recording_service.stop(job.receiver_id)
            started = False
            job.status = "done"
        except asyncio.CancelledError:
            # Cancelled (job.cancel()) while a recording it started is still
            # running -- stop it rather than leaving it recording forever
            # with nothing left to ever call stop().
            if started:
                await self._recording_service.stop(job.receiver_id)
            raise
        except RecordingAlreadyActiveError:
            job.status = "failed"
            logger.warning("Scheduled recording for '%s' skipped: already recording", job.receiver_id)
        except Exception:
            job.status = "failed"
            logger.exception("Scheduled recording failed for '%s'", job.receiver_id)
        finally:
            self._tasks.pop(job_id, None)

    def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
