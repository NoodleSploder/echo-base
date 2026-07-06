"""Application configuration.

Settings are assembled from, in order of precedence (highest first):

1. Explicit constructor keyword arguments (mainly used in tests).
2. Environment variables prefixed ``ECHO_BASE_`` (nested via ``__``,
   e.g. ``ECHO_BASE_SERVER__PORT=9000``).
3. ``config/config.yaml`` (or the path in ``ECHO_BASE_CONFIG_FILE``).
4. Built-in field defaults below.

This lets an operator run Echo Base with zero configuration files,
override specifics with a YAML file, and still short-circuit anything
via the environment for containerized/CI deployments.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_FILE = REPO_ROOT / "config" / "config.yaml"
DATA_DIR = REPO_ROOT / "data"

# Deliberately obvious placeholder so it's impossible to miss in logs or
# to mistake for a real secret. See lifespan startup checks in app.main.
DEFAULT_INSECURE_SECRET_KEY = "insecure-development-secret-key-change-me"


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8088
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    # Hostnames the Vite dev server should accept (beyond localhost),
    # e.g. when reached through a reverse proxy or tunnel. Read by
    # start.sh and passed to frontend/vite.config.ts as
    # ECHO_BASE_ALLOWED_HOSTS -- see Vite's server.allowedHosts.
    allowed_hosts: list[str] = Field(default_factory=list)


class DatabaseSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'echo-base.db'}"
    echo: bool = False


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_format: bool = False
    directory: str = str(REPO_ROOT / "logs")
    filename: str = "echo-base.log"


class SecuritySettings(BaseModel):
    secret_key: str = DEFAULT_INSECURE_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    cookie_name: str = "echo_base_session"


class PluginSettings(BaseModel):
    directory: str = str(REPO_ROOT / "plugins")
    # Explicitly disabled plugin ids: {"rtl_sdr": false}. Absent entries
    # default to enabled.
    enabled: dict[str, bool] = Field(default_factory=dict)
    # Per-plugin configuration blocks, keyed by plugin id.
    settings: dict[str, dict[str, Any]] = Field(default_factory=dict)


class RecordingSettings(BaseModel):
    directory: str = str(DATA_DIR / "recordings")


class YamlConfigSource(PydanticBaseSettingsSource):
    """Pydantic-settings source that reads a single YAML file, if present."""

    def __init__(self, settings_cls: type[BaseSettings], yaml_file: Path) -> None:
        super().__init__(settings_cls)
        self._yaml_file = yaml_file

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # Required by PydanticBaseSettingsSource; unused since __call__
        # returns the whole document at once.
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        if not self._yaml_file.exists():
            return {}
        with self._yaml_file.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return data or {}


class Settings(BaseSettings):
    """Root application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="ECHO_BASE_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = "development"
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    recordings: RecordingSettings = Field(default_factory=RecordingSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_file = Path(os.environ.get("ECHO_BASE_CONFIG_FILE", DEFAULT_CONFIG_FILE))
        return (
            init_settings,
            env_settings,
            YamlConfigSource(settings_cls, yaml_file),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
