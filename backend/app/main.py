"""FastAPI application factory and lifespan wiring."""
from __future__ import annotations

import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.router import api_router
from app.api.routes.events import router as ws_router
from app.core.config import DATA_DIR, DEFAULT_INSECURE_SECRET_KEY, Settings, get_settings
from app.core.events import EventBus
from app.core.exceptions import EchoBaseError
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db import session as db_session
from app.db.models.user import User, UserRole
from app.plugins.manager import PluginManager
from app.schemas.common import fail
from app.services.receiver_service import ReceiverService
from app.services.recording_service import RecordingService
from app.services.signal_history import persist_signal_detected
from app.services.stream_service import StreamService
from app.websocket.manager import ConnectionManager

logger = get_logger("echo_base.app")


async def _bootstrap_admin(settings: Settings) -> None:
    """Create a default administrator account on a brand-new install."""
    factory = db_session.get_session_factory()
    async with factory() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        password = secrets.token_urlsafe(12)
        admin = User(
            username="admin",
            hashed_password=hash_password(password),
            role=UserRole.ADMINISTRATOR,
            must_change_password=True,
        )
        db.add(admin)
        await db.commit()

        logger.warning(
            "No users existed; created default administrator account.",
            extra={"metadata": {"username": "admin"}},
        )
        print(
            "\n"
            "==============================================================\n"
            " Echo Base: created default administrator account\n"
            "   username: admin\n"
            f"   password: {password}\n"
            " You will be required to change this password after login.\n"
            "==============================================================\n"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    logger.info(
        "Starting Echo Base %s", __version__, extra={"metadata": {"environment": settings.environment}}
    )

    if settings.security.secret_key == DEFAULT_INSECURE_SECRET_KEY:
        if settings.environment == "production":
            raise RuntimeError(
                "Refusing to start in production with the default insecure secret_key. "
                "Set security.secret_key in config/config.yaml or ECHO_BASE_SECURITY__SECRET_KEY."
            )
        logger.warning("Using the default insecure secret_key; set one before deploying to production.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_session.init_engine(settings)
    await db_session.create_all()

    event_bus = EventBus()
    event_bus.bind_loop(asyncio.get_running_loop())
    connection_manager = ConnectionManager(event_bus)
    event_bus.subscribe("SignalDetected", persist_signal_detected)

    disabled_ids = {plugin_id for plugin_id, enabled in settings.plugins.enabled.items() if not enabled}
    plugin_manager = PluginManager(
        directory=Path(settings.plugins.directory),
        event_bus=event_bus,
        plugin_settings=settings.plugins.settings,
        disabled=disabled_ids,
    )
    plugin_manager.load_all()

    receiver_service = ReceiverService(plugin_manager)
    stream_service = StreamService(receiver_service, event_bus)
    recording_service = RecordingService(stream_service, Path(settings.recordings.directory))

    app.state.settings = settings
    app.state.event_bus = event_bus
    app.state.connection_manager = connection_manager
    app.state.plugin_manager = plugin_manager
    app.state.receiver_service = receiver_service
    app.state.stream_service = stream_service
    app.state.recording_service = recording_service

    await _bootstrap_admin(settings)

    logger.info(
        "Echo Base startup complete",
        extra={"metadata": {"plugins_loaded": len(plugin_manager.plugins)}},
    )

    yield

    logger.info("Shutting down Echo Base")
    recording_service.shutdown()
    stream_service.shutdown()
    plugin_manager.shutdown_all()
    await db_session.dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Echo Base",
        description="Open-source Radio Operations Platform API.",
        version=__version__,
        lifespan=lifespan,
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(EchoBaseError)
    async def handle_echo_base_error(request: Request, exc: EchoBaseError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=fail(exc.code, exc.message))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=fail("HTTP_ERROR", str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=fail("VALIDATION_ERROR", "Request validation failed.", details=exc.errors()),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=fail("INTERNAL_ERROR", "An unexpected error occurred."))

    app.include_router(api_router)
    app.include_router(ws_router)

    return app


app = create_app()
