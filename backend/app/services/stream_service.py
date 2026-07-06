"""One raw-IQ capture per receiver, feeding both the spectrum FFT and
software audio demodulation.

Earlier revisions ran spectrum and audio as two independent
subprocesses against the same physical device (`rtl_sdr` for the FFT,
`rtl_fm` for demod) -- which meant opening the Spectrum Monitor and
hitting Listen on the same receiver at the same time raced for
exclusive access to one USB dongle and one of the two would silently
fail. StreamService instead opens exactly one `open_iq_stream` per
receiver (the same primitive SpectrumService always used) and derives
both the FFT and the demodulated audio from the same samples in
Python, via `app.services.dsp`. A receiver's hardware is now claimed
by at most one capture, however many spectrum/audio subscribers are
watching it.

`_ReceiverCapture` doesn't know or care whether its samples come from
real hardware or a recorded `.iq` file on disk (`register_playback`) --
both are just something that produces an `IqStreamHandle`. This is
what lets a recording be "played back" through the exact same
spectrum/audio/decoder pipeline live receivers use, with no separate
code path.
"""
from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.core.events import EventBus
from app.plugins.receiver import IqStreamHandle
from app.services.decoders.afsk import Afsk1200Decoder
from app.services.decoders.aprs_position import parse_aprs_position
from app.services.decoders.ax25 import format_callsign, format_path, parse_ax25_frame
from app.services.decoders.same import SameDecoder, parse_same_header
from app.services.decoders.same_codes import describe_event, describe_location
from app.services.dsp import AUDIO_SAMPLE_RATE_HZ, DEMODULATORS, fm_discriminator
from app.services.receiver_service import ReceiverService

logger = logging.getLogger("echo_base.stream")

READ_SAMPLES = 4800  # ~20-100ms of IQ per read, depending on capture rate
FFT_SIZE = 1024
OUTPUT_BINS = 512
QUEUE_SIZE = 8


def _rebin(magnitudes_db: np.ndarray, bins: int) -> np.ndarray:
    """Averages an FFT magnitude array down to a fixed number of output bins."""
    if len(magnitudes_db) == bins:
        return magnitudes_db
    edges = np.linspace(0, len(magnitudes_db), bins + 1).astype(int)
    return np.array(
        [magnitudes_db[edges[i] : max(edges[i + 1], edges[i] + 1)].mean() for i in range(bins)],
        dtype=np.float32,
    )


async def _push(queue: asyncio.Queue[bytes], payload: bytes) -> None:
    if queue.full():
        queue.get_nowait()
    queue.put_nowait(payload)


class _RecordingIqStream:
    """An `IqStreamHandle` backed by a recorded `.iq` file instead of live
    hardware -- read() returning b"" at EOF naturally ends the capture's
    run loop exactly the way a disconnected live source would, no special
    "end of playback" handling needed."""

    def __init__(self, path: Path, sample_rate_hz: int) -> None:
        self._file = path.open("rb")
        self.sample_rate_hz = sample_rate_hz

    def read(self, n: int) -> bytes:
        return self._file.read(n)

    def close(self) -> None:
        self._file.close()


class _ReceiverCapture:
    """Owns one receiver's IQ capture and fans computed frames out to
    however many spectrum/audio subscribers are currently watching it."""

    def __init__(
        self,
        receiver_id: str,
        open_handle: Callable[[], IqStreamHandle],
        loop: asyncio.AbstractEventLoop,
        event_bus: EventBus,
    ) -> None:
        self.receiver_id = receiver_id
        self._open_handle = open_handle
        self._loop = loop
        self._event_bus = event_bus
        self._spectrum_subscribers: set[asyncio.Queue[bytes]] = set()
        self._audio_subscribers: dict[str, set[asyncio.Queue[bytes]]] = {}
        self._iq_subscribers: set[asyncio.Queue[bytes]] = set()
        self._aprs_enabled = False
        self._aprs_decoder: Afsk1200Decoder | None = None
        self._same_enabled = False
        self._same_decoder: SameDecoder | None = None
        self._handle: IqStreamHandle | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def is_idle(self) -> bool:
        return (
            not self._spectrum_subscribers
            and not any(self._audio_subscribers.values())
            and not self._iq_subscribers
            and not self._aprs_enabled
            and not self._same_enabled
        )

    @property
    def sample_rate_hz(self) -> int | None:
        return self._handle.sample_rate_hz if self._handle is not None else None

    def enable_aprs(self) -> None:
        self._aprs_enabled = True

    def disable_aprs(self) -> None:
        self._aprs_enabled = False
        self._aprs_decoder = None

    def enable_same(self) -> None:
        self._same_enabled = True

    def disable_same(self) -> None:
        self._same_enabled = False
        self._same_decoder = None

    def add_spectrum_subscriber(self, queue: asyncio.Queue[bytes]) -> None:
        self._spectrum_subscribers.add(queue)

    def remove_spectrum_subscriber(self, queue: asyncio.Queue[bytes]) -> None:
        self._spectrum_subscribers.discard(queue)

    def add_iq_subscriber(self, queue: asyncio.Queue[bytes]) -> None:
        self._iq_subscribers.add(queue)

    def remove_iq_subscriber(self, queue: asyncio.Queue[bytes]) -> None:
        self._iq_subscribers.discard(queue)

    def add_audio_subscriber(self, mode: str, queue: asyncio.Queue[bytes]) -> None:
        self._audio_subscribers.setdefault(mode, set()).add(queue)

    def remove_audio_subscriber(self, mode: str, queue: asyncio.Queue[bytes]) -> None:
        subscribers = self._audio_subscribers.get(mode)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if not subscribers:
            del self._audio_subscribers[mode]

    def start(self) -> None:
        self._handle = self._open_handle()
        self._thread = threading.Thread(
            target=self._run, name=f"capture-{self.receiver_id}", daemon=True
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
        sample_rate_hz = self._handle.sample_rate_hz
        decimation = max(1, round(sample_rate_hz / AUDIO_SAMPLE_RATE_HZ))
        bytes_per_read = READ_SAMPLES * 2  # interleaved uint8 I/Q pairs
        window = np.hanning(FFT_SIZE).astype(np.float32)

        try:
            while not self._stop_event.is_set():
                raw = self._handle.read(bytes_per_read)
                if not raw:
                    break

                if self._iq_subscribers:
                    self._broadcast(self._iq_subscribers, raw)

                samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
                real = (samples[0::2] - 127.5) / 127.5
                imag = (samples[1::2] - 127.5) / 127.5
                complex_samples = real + 1j * imag

                if self._spectrum_subscribers and len(complex_samples) >= FFT_SIZE:
                    windowed = complex_samples[-FFT_SIZE:] * window
                    spectrum = np.fft.fftshift(np.fft.fft(windowed))
                    magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-9)
                    frame = _rebin(magnitude_db, OUTPUT_BINS).tobytes()
                    self._broadcast(self._spectrum_subscribers, frame)

                for mode, subscribers in list(self._audio_subscribers.items()):
                    if not subscribers:
                        continue
                    demodulate = DEMODULATORS[mode]
                    chunk = demodulate(complex_samples, decimation)
                    if chunk:
                        self._broadcast(subscribers, chunk)

                if self._aprs_enabled:
                    self._decode_aprs(complex_samples, decimation)

                if self._same_enabled:
                    self._decode_same(complex_samples, decimation)
        except Exception:
            logger.exception("Capture worker for '%s' crashed", self.receiver_id)
        finally:
            self._stop_event.set()

    def _decode_aprs(self, complex_samples: np.ndarray, decimation: int) -> None:
        if self._aprs_decoder is None:
            self._aprs_decoder = Afsk1200Decoder(AUDIO_SAMPLE_RATE_HZ)
        audio = fm_discriminator(complex_samples, decimation)
        for raw_frame in self._aprs_decoder.feed(audio):
            frame = parse_ax25_frame(raw_frame)
            if frame is None:
                continue  # bad FCS -- a wrong bit-sync phase guess, not a real packet
            position = parse_aprs_position(frame.info)
            data = {
                "source": format_callsign(frame.source),
                "destination": format_callsign(frame.destination),
                "path": format_path(frame),
                "info": frame.info.decode("ascii", errors="replace"),
            }
            if position is not None:
                # Only the "uncompressed" position format is parsed (see
                # decoders/aprs_position.py) -- compressed and Mic-E
                # position reports are common in real traffic but not
                # decoded yet, so most real packets won't carry these.
                data["latitude"] = position.latitude
                data["longitude"] = position.longitude
                data["symbol"] = f"{position.symbol_table}{position.symbol_code}"
            self._event_bus.emit("AprsPacket", source=self.receiver_id, data=data)

    def _decode_same(self, complex_samples: np.ndarray, decimation: int) -> None:
        if self._same_decoder is None:
            self._same_decoder = SameDecoder(AUDIO_SAMPLE_RATE_HZ)
        audio = fm_discriminator(complex_samples, decimation)
        for header in self._same_decoder.feed(audio):
            fields = parse_same_header(header)
            if fields is None:
                continue  # doesn't structurally fit -- a wrong bit-sync phase guess
            self._event_bus.emit(
                "SameAlert",
                source=self.receiver_id,
                data={
                    **fields,
                    "header": header,
                    "event_name": describe_event(fields["event_code"]),
                    "location_names": [describe_location(loc) for loc in fields["locations"]],
                },
            )

    def _broadcast(self, subscribers: set[asyncio.Queue[bytes]], payload: bytes) -> None:
        for queue in list(subscribers):
            self._loop.call_soon_threadsafe(asyncio.ensure_future, _push(queue, payload))


class StreamService:
    """Owns one `_ReceiverCapture` per receiver (or registered playback
    source) that currently has at least one subscriber."""

    def __init__(self, receiver_service: ReceiverService, event_bus: EventBus) -> None:
        self._receiver_service = receiver_service
        self._event_bus = event_bus
        self._captures: dict[str, _ReceiverCapture] = {}
        self._playback_sources: dict[str, tuple[Path, int]] = {}
        self._lock = asyncio.Lock()

    def register_playback(self, playback_id: str, path: Path, sample_rate_hz: int) -> None:
        """Makes a recorded `.iq` file subscribable through `playback_id` as
        if it were a receiver -- `subscribe_spectrum`/`subscribe_audio`/
        `enable_aprs`/etc. all work on it unchanged."""
        self._playback_sources[playback_id] = (path, sample_rate_hz)

    async def unregister_playback(self, playback_id: str) -> None:
        self._playback_sources.pop(playback_id, None)
        async with self._lock:
            capture = self._captures.pop(playback_id, None)
        if capture is not None:
            await asyncio.to_thread(capture.stop)

    async def _get_or_create(self, receiver_id: str) -> _ReceiverCapture:
        capture = self._captures.get(receiver_id)
        if capture is None:
            playback_source = self._playback_sources.get(receiver_id)
            if playback_source is not None:
                path, sample_rate_hz = playback_source
                open_handle: Callable[[], IqStreamHandle] = lambda: _RecordingIqStream(  # noqa: E731
                    path, sample_rate_hz
                )
            else:
                plugin = await self._receiver_service.resolve_plugin(receiver_id)
                open_handle = lambda: plugin.open_iq_stream(receiver_id)  # noqa: E731
            capture = _ReceiverCapture(receiver_id, open_handle, asyncio.get_running_loop(), self._event_bus)
            await asyncio.to_thread(capture.start)
            self._captures[receiver_id] = capture
        return capture

    async def _drop_if_idle(self, receiver_id: str) -> None:
        capture = self._captures.get(receiver_id)
        if capture is not None and capture.is_idle():
            del self._captures[receiver_id]
            await asyncio.to_thread(capture.stop)

    async def subscribe_spectrum(self, receiver_id: str) -> asyncio.Queue[bytes]:
        """Raises whatever `ReceiverService.resolve_plugin` / `open_iq_stream` raise
        (e.g. ReceiverNotFoundError, or NotImplementedError if the plugin can't stream)."""
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=QUEUE_SIZE)
        async with self._lock:
            capture = await self._get_or_create(receiver_id)
            capture.add_spectrum_subscriber(queue)
        return queue

    async def unsubscribe_spectrum(self, receiver_id: str, queue: asyncio.Queue[bytes]) -> None:
        async with self._lock:
            capture = self._captures.get(receiver_id)
            if capture is None:
                return
            capture.remove_spectrum_subscriber(queue)
            await self._drop_if_idle(receiver_id)

    async def subscribe_iq(self, receiver_id: str) -> asyncio.Queue[bytes]:
        """Raw interleaved uint8 I/Q bytes, unprocessed -- e.g. for IQ recording."""
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=QUEUE_SIZE)
        async with self._lock:
            capture = await self._get_or_create(receiver_id)
            capture.add_iq_subscriber(queue)
        return queue

    async def unsubscribe_iq(self, receiver_id: str, queue: asyncio.Queue[bytes]) -> None:
        async with self._lock:
            capture = self._captures.get(receiver_id)
            if capture is None:
                return
            capture.remove_iq_subscriber(queue)
            await self._drop_if_idle(receiver_id)

    def get_sample_rate(self, receiver_id: str) -> int | None:
        """The capture's actual IQ sample rate, once a capture exists for
        this receiver (i.e. after any subscribe_* call) -- None otherwise."""
        capture = self._captures.get(receiver_id)
        return capture.sample_rate_hz if capture is not None else None

    async def subscribe_audio(self, receiver_id: str, mode: str) -> asyncio.Queue[bytes]:
        """`mode` must be a key in `app.services.dsp.DEMODULATORS`."""
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=QUEUE_SIZE)
        async with self._lock:
            capture = await self._get_or_create(receiver_id)
            capture.add_audio_subscriber(mode, queue)
        return queue

    async def unsubscribe_audio(self, receiver_id: str, mode: str, queue: asyncio.Queue[bytes]) -> None:
        async with self._lock:
            capture = self._captures.get(receiver_id)
            if capture is None:
                return
            capture.remove_audio_subscriber(mode, queue)
            await self._drop_if_idle(receiver_id)

    async def enable_aprs(self, receiver_id: str) -> None:
        """Idempotent: decoded packets are emitted as `AprsPacket` events on
        the shared EventBus (source=receiver_id), not returned here --
        anything already listening to /ws/events (Activity Feed, System
        Log) picks them up automatically, no dedicated channel needed."""
        async with self._lock:
            capture = await self._get_or_create(receiver_id)
            capture.enable_aprs()

    async def disable_aprs(self, receiver_id: str) -> None:
        async with self._lock:
            capture = self._captures.get(receiver_id)
            if capture is None:
                return
            capture.disable_aprs()
            await self._drop_if_idle(receiver_id)

    async def enable_same(self, receiver_id: str) -> None:
        """Same idempotent/EventBus-based shape as `enable_aprs`, emitting
        `SameAlert` events instead."""
        async with self._lock:
            capture = await self._get_or_create(receiver_id)
            capture.enable_same()

    async def disable_same(self, receiver_id: str) -> None:
        async with self._lock:
            capture = self._captures.get(receiver_id)
            if capture is None:
                return
            capture.disable_same()
            await self._drop_if_idle(receiver_id)

    def is_active(self, receiver_id: str) -> bool:
        """Whether IQ is actually being captured for this receiver right now
        (someone is watching its spectrum or listening to it) -- distinct
        from `ReceiverStatus.state`, which today is just a manual flag
        toggled by start()/stop() and doesn't know about this at all."""
        return receiver_id in self._captures

    def shutdown(self) -> None:
        """Stops every active capture; called once on application shutdown."""
        for capture in self._captures.values():
            capture.stop()
        self._captures.clear()
