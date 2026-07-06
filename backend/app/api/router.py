"""Aggregates every REST/WebSocket router under one include-able object."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, config, events, plugins, receivers, system, users

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(config.router)
api_router.include_router(receivers.router)
api_router.include_router(plugins.router)
api_router.include_router(events.router)
