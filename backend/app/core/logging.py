"""Structured logging setup shared by the application and its plugins."""
from __future__ import annotations

import json
import logging
import logging.config
from pathlib import Path
from typing import Any

from app.core.config import Settings


class JsonFormatter(logging.Formatter):
    """Emits one JSON object per line: timestamp, level, component, event, metadata."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "component": record.name,
            "event": record.getMessage(),
        }
        metadata = getattr(record, "metadata", None)
        if metadata:
            payload["metadata"] = metadata
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    log_dir = Path(settings.logging.directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter_key = "json" if settings.logging.json_format else "standard"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                },
                "json": {"()": f"{__name__}.JsonFormatter"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_key,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": formatter_key,
                    "filename": str(log_dir / settings.logging.filename),
                    "maxBytes": 10_000_000,
                    "backupCount": 5,
                },
            },
            "root": {
                "level": settings.logging.level,
                "handlers": ["console", "file"],
            },
            "loggers": {
                "uvicorn": {"level": settings.logging.level, "propagate": True},
                "uvicorn.access": {"level": settings.logging.level, "propagate": True},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
