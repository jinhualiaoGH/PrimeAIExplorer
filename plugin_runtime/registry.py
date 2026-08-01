from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any, Mapping

from kernel.exceptions import ConfigurationError
from plugin_runtime.manifest import PluginManifest


@dataclass
class ManifestRegistry:
    _manifests: dict[str, PluginManifest] = field(
        default_factory=dict
    )

    def register(
        self,
        manifest: PluginManifest,
        *,
        replace: bool = False,
    ) -> None:
        plugin_id = manifest.plugin_id
        if plugin_id in self._manifests and not replace:
            raise ConfigurationError(
                f"Manifest is already registered: {plugin_id}"
            )
        self._manifests[plugin_id] = manifest

    def resolve(self, plugin_id: str) -> PluginManifest:
        normalized = self._normalize_id(plugin_id)
        if normalized not in self._manifests:
            raise ConfigurationError(
                f"Manifest is not registered: {normalized}"
            )
        return self._manifests[normalized]

    def enabled(self) -> tuple[PluginManifest, ...]:
        return tuple(
            manifest
            for _, manifest in sorted(self._manifests.items())
            if manifest.enabled
        )

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._manifests))

    def load_file(
        self,
        path: str | Path,
        *,
        replace: bool = False,
    ) -> tuple[PluginManifest, ...]:
        registry_path = Path(path)
        if not registry_path.is_file():
            raise ConfigurationError(
                f"Manifest registry file does not exist: {registry_path}"
            )
        try:
            payload = json.loads(
                registry_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(
                f"Could not read plugin registry: {registry_path}"
            ) from exc

        entries = self._entries(payload)
        manifests = tuple(
            PluginManifest.from_mapping(entry)
            for entry in entries
        )
        for manifest in manifests:
            self.register(manifest, replace=replace)
        return manifests

    @staticmethod
    def _entries(payload: Any) -> list[Mapping[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, Mapping):
            entries = payload.get("plugins")
            if isinstance(entries, list):
                return entries
        raise ConfigurationError(
            "Registry JSON must be a list or contain a plugins list."
        )

    @staticmethod
    def _normalize_id(plugin_id: str) -> str:
        if not isinstance(plugin_id, str):
            raise ConfigurationError("plugin_id must be text.")
        normalized = plugin_id.strip()
        if not normalized:
            raise ConfigurationError(
                "plugin_id must not be empty."
            )
        return normalized
