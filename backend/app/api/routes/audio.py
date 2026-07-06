"""Live audio WebSocket: demodulated PCM16 mono frames for one receiver.

Same shape as spectrum.py's `/ws/spectrum/{receiver_id}` -- per-receiver
socket, lazily starts/stops the underlying IQ capture based on
subscriber count (see StreamService) -- but for software-demodulated
audio instead of an FFT. Both sockets share the same underlying
capture per receiver, so a receiver's hardware is never claimed twice.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import authenticate
from app.core.exceptions import EchoBaseError
from app.db.session import get_session_factory
from app.services.dsp import DEMODULATORS
from app.services.stream_service import StreamService

router = APIRouter(tags=["audio"])


@router.websocket("/ws/audio/{receiver_id}")
async def audio_stream(websocket: WebSocket, receiver_id: str, mode: str = "fm") -> None:
    settings = websocket.app.state.settings
    stream_service: StreamService = websocket.app.state.stream_service
    session_factory = get_session_factory()

    if mode not in DEMODULATORS:
        await websocket.close(code=4400)
        return

    async with session_factory() as db:
        try:
            await authenticate(websocket.cookies, websocket.headers, settings, db)
        except Exception:
            await websocket.close(code=4401)
            return

    try:
        queue = await stream_service.subscribe_audio(receiver_id, mode)
    except EchoBaseError:
        await websocket.close(code=4404)
        return
    except NotImplementedError:
        await websocket.close(code=4405)
        return
    except Exception:
        await websocket.close(code=1011)
        return

    await websocket.accept()
    try:
        while True:
            chunk = await queue.get()
            await websocket.send_bytes(chunk)
    except WebSocketDisconnect:
        pass
    finally:
        await stream_service.unsubscribe_audio(receiver_id, mode, queue)
