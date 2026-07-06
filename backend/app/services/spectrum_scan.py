"""Automated multi-frequency sweep (Phase 2/4: spectrum scanning).

Cycles a receiver through a fixed list of frequencies on a timer,
dwelling on each for `dwell_seconds` before retuning to the next --
the classic "scan list" a conventional scanner radio offers, built on
top of `ReceiverService.tune` (the same call the manual Tune button
uses) rather than any new hardware primitive.

Deliberately just retunes on a timer; it doesn't itself decide
anything is "busy" (that's what `enable_signal_detection`/
`enable_occupancy` are for -- a scan can be combined with either by a
caller/UI, not fused into one subsystem here).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.services.receiver_service import ReceiverService

logger = logging.getLogger("echo_base.spectrum_scan")


@dataclass
class ScanState:
    frequencies: list[int]
    dwell_seconds: float
    index: int = 0


class SpectrumScanService:
    def __init__(self, receiver_service: ReceiverService) -> None:
        self._receiver_service = receiver_service
        self._states: dict[str, ScanState] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def start(self, receiver_id: str, frequencies: list[int], dwell_seconds: float) -> None:
        if not frequencies:
            raise ValueError("frequencies must not be empty.")
        if dwell_seconds <= 0:
            raise ValueError("dwell_seconds must be positive.")
        self.stop(receiver_id)
        state = ScanState(frequencies=list(frequencies), dwell_seconds=dwell_seconds)
        self._states[receiver_id] = state
        self._tasks[receiver_id] = asyncio.create_task(self._run(receiver_id, state))

    def stop(self, receiver_id: str) -> None:
        self._states.pop(receiver_id, None)
        task = self._tasks.pop(receiver_id, None)
        if task is not None:
            task.cancel()

    def status(self, receiver_id: str) -> dict | None:
        state = self._states.get(receiver_id)
        if state is None:
            return None
        return {
            "frequencies": state.frequencies,
            "dwell_seconds": state.dwell_seconds,
            "current_index": state.index,
            "current_frequency_hz": state.frequencies[state.index],
        }

    async def _run(self, receiver_id: str, state: ScanState) -> None:
        try:
            while True:
                frequency = state.frequencies[state.index]
                try:
                    await self._receiver_service.tune(receiver_id, frequency)
                except Exception:
                    logger.exception("Scan tune failed for '%s' at %d Hz", receiver_id, frequency)
                await asyncio.sleep(state.dwell_seconds)
                state.index = (state.index + 1) % len(state.frequencies)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Spectrum scan crashed for '%s'", receiver_id)

    def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
