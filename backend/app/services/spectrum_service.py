"""Computes FFT magnitude spectra from receiver plugins' raw IQ streams
and fans them out to WebSocket subscribers.

Each receiver's IQ capture (a blocking subprocess/hardware read, per
``ReceiverPlugin.open_iq_stream``) runs in its own background thread --
never on the asyncio event loop, mirroring EventBus.emit's
thread-to-loop handoff via ``run_coroutine_threadsafe``. A capture is
started lazily on the first subscriber for a receiver and torn down
once the last one disconnects, so an unwatched dashboard doesn't tie
up a physical SDR that operators may want to use elsewhere.
"""
from __future__ import annotations

import asyncio
import logging
import threading

import numpy as np

from app.plugins.receiver import IqStreamHandle, ReceiverPlugin
from app.services.receiver_service import ReceiverService

logger = logging.getLogger("echo_base.spectrum")

FFT_SIZE = 1024
OUTPUT_BINS = 512
QUEUE_SIZE = 4


def _rebin(magnitudes_db: np.ndarray, bins: int) -> np.ndarray:
    """Averages an FFT magnitude array down to a fixed number of output bins."""
    if len(magnitudes_db) == bins:
        return magnitudes_db
    edges = np.linspace(0, len(magnitudes_db), bins + 1).astype(int)
    return np.array(
        [magnitudes_db[edges[i] : max(edges[i + 1], edges[i] + 1)].mean() for i in range(bins)],
        dtype=np.float32,
    )


async def _push(queue: asyncio.Queue[bytes], frame: bytes) -> None:
    if queue.full():
        queue.get_nowait()
    queue.put_nowait(frame)


class _StreamWorker:
    """Owns one plugin IQ capture and broadcasts computed frames to its subscribers."""

    def __init__(self, receiver_id: str, plugin: ReceiverPlugin, loop: asyncio.AbstractEventLoop) -> None:
        self.receiver_id = receiver_id
        self._plugin = plugin
        self._loop = loop
        self._subscribers: set[asyncio.Queue[bytes]] = set()
        self._handle: IqStreamHandle | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def add_subscriber(self, queue: asyncio.Queue[bytes]) -> None:
        self._subscribers.add(queue)

    def remove_subscriber(self, queue: asyncio.Queue[bytes]) -> bool:
        """Returns True once no subscribers remain (caller should then stop() this worker)."""
        self._subscribers.discard(queue)
        return not self._subscribers

    def start(self) -> None:
        self._handle = self._plugin.open_iq_stream(self.receiver_id)
        self._thread = threading.Thread(
            target=self._run, name=f"spectrum-{self.receiver_id}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._handle is not None:
            self._handle.close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        assert self._handle is not None
        bytes_per_frame = FFT_SIZE * 2  # interleaved uint8 I/Q pairs
        window = np.hanning(FFT_SIZE).astype(np.float32)
        try:
            while not self._stop_event.is_set():
                raw = self._handle.read(bytes_per_frame)
                if not raw:
                    break
                if len(raw) < bytes_per_frame:
                    continue
                samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
                iq = (samples - 127.5) / 127.5
                complex_samples = iq[0::2] + 1j * iq[1::2]
                spectrum = np.fft.fftshift(np.fft.fft(complex_samples * window))
                magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-9)
                frame = _rebin(magnitude_db, OUTPUT_BINS).tobytes()
                self._broadcast(frame)
        except Exception:
            logger.exception("Spectrum worker for '%s' crashed", self.receiver_id)
        finally:
            self._stop_event.set()

    def _broadcast(self, frame: bytes) -> None:
        for queue in list(self._subscribers):
            self._loop.call_soon_threadsafe(asyncio.ensure_future, _push(queue, frame))


class SpectrumService:
    """Owns one `_StreamWorker` per receiver that currently has at least one subscriber."""

    def __init__(self, receiver_service: ReceiverService) -> None:
        self._receiver_service = receiver_service
        self._workers: dict[str, _StreamWorker] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, receiver_id: str) -> asyncio.Queue[bytes]:
        """Raises whatever `ReceiverService.resolve_plugin` / `open_iq_stream` raise
        (e.g. ReceiverNotFoundError, or NotImplementedError if the plugin can't stream)."""
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=QUEUE_SIZE)
        async with self._lock:
            worker = self._workers.get(receiver_id)
            if worker is None:
                plugin = await self._receiver_service.resolve_plugin(receiver_id)
                worker = _StreamWorker(receiver_id, plugin, asyncio.get_running_loop())
                await asyncio.to_thread(worker.start)
                self._workers[receiver_id] = worker
            worker.add_subscriber(queue)
        return queue

    async def unsubscribe(self, receiver_id: str, queue: asyncio.Queue[bytes]) -> None:
        async with self._lock:
            worker = self._workers.get(receiver_id)
            if worker is None:
                return
            if worker.remove_subscriber(queue):
                del self._workers[receiver_id]
                await asyncio.to_thread(worker.stop)

    def shutdown(self) -> None:
        """Stops every active capture; called once on application shutdown."""
        for worker in self._workers.values():
            worker.stop()
        self._workers.clear()
