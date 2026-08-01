from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
import re

from kernel.exceptions import ConfigurationError
from kernel.serialization import normalize, stable_sha256


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_IMPORT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def _text(name: str, value: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{name} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{name} must not be empty.")
    if pattern.fullmatch(normalized) is None:
        raise ConfigurationError(
            f"{name} contains unsupported characters: {value!r}"
        )
    return normalized


@dataclass(frozen=True)
class PluginManifest:
    schema_version: str
    plugin_id: str
    plugin_version: str
    module: str
    class_name: str
    capabilities: tuple[str, ...]
    enabled: bool
    configuration: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text("schema_version", self.schema_version, _ID),
        )
        object.__setattr__(
            self,
            "plugin_id",
            _text("plugin_id", self.plugin_id, _ID),
        )
        object.__setattr__(
            self,
            "plugin_version",
            _text("plugin_version", self.plugin_version, _ID),
        )
        object.__setattr__(
            self,
            "module",
            _text("module", self.module, _IMPORT),
        )
        object.__setattr__(
            self,
            "class_name",
            _text("class_name", self.class_name, _ID),
        )
        if not isinstance(self.enabled, bool):
            raise ConfigurationError("enabled must be boolean.")
        if not isinstance(self.capabilities, tuple):
            object.__setattr__(
                self,
                "capabilities",
                tuple(self.capabilities),
            )
        normalized_capabilities = tuple(
            sorted(
                {
                    _text("capability", value, _ID)
                    for value in self.capabilities
                }
            )
        )
        if not normalized_capabilities:
            raise ConfigurationError(
                "At least one capability is required."
            )
        object.__setattr__(
            self,
            "capabilities",
            normalized_capabilities,
        )
        if not isinstance(self.configuration, Mapping):
            raise ConfigurationError(
                "configuration must be a mapping."
            )
        object.__setattr__(
            self,
            "configuration",
            MappingProxyType(
                normalize(dict(self.configuration))
            ),
        )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "PluginManifest":
        if not isinstance(value, Mapping):
            raise ConfigurationError(
                "Plugin manifest must be a mapping."
            )
        required = {
            "plugin_id",
            "plugin_version",
            "module",
            "class_name",
            "capabilities",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ConfigurationError(
                f"Plugin manifest is missing fields: {missing}"
            )
        return cls(
            schema_version=str(
                value.get("schema_version", "1.0")
            ),
            plugin_id=value["plugin_id"],
            plugin_version=value["plugin_version"],
            module=value["module"],
            class_name=value["class_name"],
            capabilities=tuple(value["capabilities"]),
            enabled=value.get("enabled", True),
            configuration=value.get("configuration", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "module": self.module,
            "class_name": self.class_name,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
            "configuration": dict(self.configuration),
        }

    @property
    def manifest_sha256(self) -> str:
        return stable_sha256(self.to_dict())
