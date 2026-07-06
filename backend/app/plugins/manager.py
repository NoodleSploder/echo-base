"""Plugin discovery, loading, and lifecycle management.

Plugins live under ``plugins/<id>/`` with a ``manifest.yaml`` and an
entry-point module (default ``plugin.py``). The entry-point module must
define exactly one subclass of :class:`~app.plugins.base.Plugin`; it is
found by inspection rather than a manifest field, keeping manifests as
simple as the example in docs/PLUGIN_API.md.
"""
from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml
from pydantic import ValidationError

from app.core.events import EventBus
from app.plugins.base import Plugin, PluginContext
from app.plugins.manifest import PluginManifest

logger = logging.getLogger("echo_base.plugins")


class PluginLoadError(RuntimeError):
    pass


class LoadedPlugin:
    def __init__(self, manifest: PluginManifest, instance: Plugin, path: Path, enabled: bool) -> None:
        self.manifest = manifest
        self.instance = instance
        self.path = path
        self.enabled = enabled


class PluginManager:
    def __init__(
        self,
        directory: Path,
        event_bus: EventBus,
        plugin_settings: dict[str, dict[str, Any]] | None = None,
        disabled: set[str] | None = None,
    ) -> None:
        self._directory = directory
        self._event_bus = event_bus
        self._plugin_settings = plugin_settings or {}
        self._disabled = disabled or set()
        self._plugins: dict[str, LoadedPlugin] = {}

    @property
    def plugins(self) -> dict[str, LoadedPlugin]:
        return self._plugins

    def discover_manifests(self) -> list[Path]:
        if not self._directory.exists():
            return []
        return sorted(self._directory.glob("*/manifest.yaml"))

    def load_all(self) -> None:
        for manifest_path in self.discover_manifests():
            try:
                self.load_plugin(manifest_path)
            except PluginLoadError:
                logger.exception("Failed to load plugin from %s", manifest_path)

    def load_plugin(self, manifest_path: Path) -> LoadedPlugin:
        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        try:
            manifest = PluginManifest(**manifest_data)
        except ValidationError as exc:
            raise PluginLoadError(f"Invalid manifest at {manifest_path}: {exc}") from exc

        plugin_dir = manifest_path.parent
        entry_path = plugin_dir / manifest.entry_point
        if not entry_path.exists():
            raise PluginLoadError(f"Entry point {entry_path} does not exist for plugin '{manifest.id}'")

        module = self._import_module(manifest.id, entry_path)
        plugin_cls = self._find_plugin_class(module)
        if plugin_cls is None:
            raise PluginLoadError(f"No Plugin subclass found in {entry_path}")

        enabled = manifest.id not in self._disabled
        context = PluginContext(
            plugin_id=manifest.id,
            config=self._plugin_settings.get(manifest.id, {}),
            logger=logging.getLogger(f"echo_base.plugins.{manifest.id}"),
            event_bus=self._event_bus,
        )
        instance = plugin_cls(context)

        loaded = LoadedPlugin(manifest=manifest, instance=instance, path=plugin_dir, enabled=enabled)
        self._plugins[manifest.id] = loaded

        if enabled:
            self._initialize(loaded)
        return loaded

    @staticmethod
    def _import_module(plugin_id: str, entry_path: Path) -> ModuleType:
        module_name = f"echo_base_plugins.{plugin_id}"
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Could not import entry point {entry_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            del sys.modules[module_name]
            raise PluginLoadError(f"Error executing plugin module {entry_path}: {exc}") from exc
        return module

    @staticmethod
    def _find_plugin_class(module: ModuleType) -> type[Plugin] | None:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj.__module__ == module.__name__:
                return obj
        return None

    def _initialize(self, loaded: LoadedPlugin) -> None:
        try:
            loaded.instance.initialize()
            logger.info(
                "Loaded plugin '%s' (%s)",
                loaded.manifest.id,
                loaded.manifest.plugin_type.value,
            )
        except Exception:
            loaded.enabled = False
            logger.exception("Plugin '%s' raised during initialize()", loaded.manifest.id)

    def get(self, plugin_id: str) -> LoadedPlugin | None:
        return self._plugins.get(plugin_id)

    def by_type(self, plugin_type: str) -> list[LoadedPlugin]:
        return [p for p in self._plugins.values() if p.enabled and p.manifest.plugin_type == plugin_type]

    def enable(self, plugin_id: str) -> LoadedPlugin:
        loaded = self._require(plugin_id)
        if not loaded.enabled:
            loaded.enabled = True
            self._initialize(loaded)
        return loaded

    def disable(self, plugin_id: str) -> LoadedPlugin:
        loaded = self._require(plugin_id)
        if loaded.enabled:
            try:
                loaded.instance.shutdown()
            except Exception:
                logger.exception("Plugin '%s' raised during shutdown()", plugin_id)
            loaded.enabled = False
        return loaded

    def reload(self, plugin_id: str) -> LoadedPlugin:
        loaded = self._require(plugin_id)
        manifest_path = loaded.path / "manifest.yaml"
        self.disable(plugin_id)
        del self._plugins[plugin_id]
        return self.load_plugin(manifest_path)

    def shutdown_all(self) -> None:
        for plugin_id in list(self._plugins):
            self.disable(plugin_id)

    def _require(self, plugin_id: str) -> LoadedPlugin:
        loaded = self._plugins.get(plugin_id)
        if loaded is None:
            raise KeyError(plugin_id)
        return loaded
