from __future__ import annotations

from dataclasses import dataclass

from kernel.exceptions import ConfigurationError
from plugin_runtime.manifest import PluginManifest
from plugin_runtime.registry import ManifestRegistry


@dataclass(frozen=True)
class CapabilityResolver:
    registry: ManifestRegistry

    def candidates(
        self,
        capability: str,
    ) -> tuple[PluginManifest, ...]:
        normalized = self._normalize(capability)
        return tuple(
            manifest
            for manifest in self.registry.enabled()
            if normalized in manifest.capabilities
        )

    def resolve(
        self,
        capability: str,
        *,
        preferred_plugin_id: str | None = None,
    ) -> PluginManifest:
        candidates = self.candidates(capability)
        if preferred_plugin_id is not None:
            preferred = preferred_plugin_id.strip()
            for manifest in candidates:
                if manifest.plugin_id == preferred:
                    return manifest
            raise ConfigurationError(
                "Preferred plugin does not provide the requested "
                f"capability: {preferred_plugin_id}"
            )
        if not candidates:
            raise ConfigurationError(
                f"No enabled plugin provides capability: {capability}"
            )
        if len(candidates) > 1:
            ids = [manifest.plugin_id for manifest in candidates]
            raise ConfigurationError(
                "Capability is ambiguous; specify preferred_plugin_id: "
                f"{ids}"
            )
        return candidates[0]

    @staticmethod
    def _normalize(capability: str) -> str:
        if not isinstance(capability, str):
            raise ConfigurationError(
                "capability must be text."
            )
        normalized = capability.strip()
        if not normalized:
            raise ConfigurationError(
                "capability must not be empty."
            )
        return normalized
