"""Async SQLAlchemy engine/session management.

The engine is a process-wide singleton created during FastAPI's lifespan
startup (see app.main) and torn down on shutdown. Swapping
``database.url`` to a Postgres DSN requires no code changes here.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.db.base import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> AsyncEngine:
    global _engine, _session_factory
    _engine = create_async_engine(settings.database.url, echo=settings.database.echo, future=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def create_all() -> None:
    """Create any tables missing from the database.

    This is the zero-configuration path used on every startup so a fresh
    checkout works immediately. Alembic (backend/alembic/) remains the
    source of truth for structured, reviewable schema migrations as the
    schema grows beyond this early stage.
    """
    if _engine is None:
        raise RuntimeError("Database engine has not been initialized yet.")

    import app.db.models  # noqa: F401  (registers models on Base.metadata)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database engine has not been initialized yet.")
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
