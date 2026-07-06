"""Live spectrum WebSocket: binary FFT magnitude frames for one receiver.

Distinct from `/ws/events` -- that's a single shared fan-out socket for
the whole app; this is per-receiver and lazily starts/stops the
underlying IQ capture based on subscriber count (see SpectrumService).
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import authenticate
from app.core.exceptions import EchoBaseError
from app.db.session import get_session_factory
from app.services.spectrum_service import SpectrumService

router = APIRouter(tags=["spectrum"])


@router.websocket("/ws/spectrum/{receiver_id}")
async def spectrum_stream(websocket: WebSocket, receiver_id: str) -> None:
    settings = websocket.app.state.settings
    spectrum_service: SpectrumService = websocket.app.state.spectrum_service
    session_factory = get_session_factory()

    async with session_factory() as db:
        try:
            await authenticate(websocket.cookies, websocket.headers, settings, db)
        except Exception:
            await websocket.close(code=4401)
            return

    try:
        queue = await spectrum_service.subscribe(receiver_id)
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
            frame = await queue.get()
            await websocket.send_bytes(frame)
    except WebSocketDisconnect:
        pass
    finally:
        await spectrum_service.unsubscribe(receiver_id, queue)
