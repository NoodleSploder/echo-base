"""Shared FastAPI dependencies: app-state accessors and auth guards."""
from __future__ import annotations

from collections.abc import Mapping

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.events import EventBus
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import TokenError, decode_session_token
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.plugins.manager import PluginManager
from app.services.noaa_swpc import SpaceWeatherService
from app.services.receiver_service import ReceiverService
from app.services.recording_service import RecordingService
from app.services.scheduled_recording import ScheduledRecordingService
from app.services.spectrum_scan import SpectrumScanService
from app.services.stream_service import StreamService
from app.services.triggered_recording import TriggeredRecordingService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


def get_plugin_manager(request: Request) -> PluginManager:
    return request.app.state.plugin_manager


def get_receiver_service(request: Request) -> ReceiverService:
    return request.app.state.receiver_service


def get_stream_service(request: Request) -> StreamService:
    return request.app.state.stream_service


def get_recording_service(request: Request) -> RecordingService:
    return request.app.state.recording_service


def get_triggered_recording_service(request: Request) -> TriggeredRecordingService:
    return request.app.state.triggered_recording_service


def get_scheduled_recording_service(request: Request) -> ScheduledRecordingService:
    return request.app.state.scheduled_recording_service


def get_spectrum_scan_service(request: Request) -> SpectrumScanService:
    return request.app.state.spectrum_scan_service


def get_space_weather_service(request: Request) -> SpaceWeatherService:
    return request.app.state.space_weather_service



async def authenticate(
    cookies: Mapping[str, str],
    headers: Mapping[str, str],
    settings: Settings,
    db: AsyncSession,
) -> User:
    """Resolve the current user from a session cookie or Bearer token.

    Shared by the HTTP dependency below and the WebSocket event stream,
    whose connection object exposes cookies/headers slightly differently
    than an HTTP Request.
    """
    token = cookies.get(settings.security.cookie_name)
    if not token:
        auth_header = headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]
    if not token:
        raise AuthenticationError("Not authenticated.")

    try:
        payload = decode_session_token(token, settings)
    except TokenError as exc:
        raise AuthenticationError("Session expired or invalid.") from exc

    user = await db.get(User, payload.get("sub"))
    if user is None or user.disabled:
        raise AuthenticationError("Account is disabled or no longer exists.")
    return user


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await authenticate(request.cookies, request.headers, settings, db)


def require_role(*roles: UserRole):
    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise AuthorizationError("You do not have permission to perform this action.")
        return user

    return _dependency
