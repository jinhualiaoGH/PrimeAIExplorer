from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
import json

from kernel.exceptions import ConfigurationError
from kernel.serialization import normalize, stable_sha256


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError("Runtime configuration must be a mapping.")
    return MappingProxyType(normalize(dict(value)))


@dataclass(frozen=True)
class RuntimeConfiguration:
    schema_version: str
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ConfigurationError("schema_version must be non-empty text.")
        object.__setattr__(self, "schema_version", self.schema_version.strip())
        object.__setattr__(self, "values", _freeze(self.values))

    @classmethod
    def empty(cls) -> "RuntimeConfiguration":
        return cls(schema_version="1.0", values={})

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, Any],
    ) -> "RuntimeConfiguration":
        return cls(schema_version="1.0", values=values)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "RuntimeConfiguration":
        source = Path(path)
        if not source.is_file():
            raise ConfigurationError(
                f"Runtime configuration file does not exist: {source}"
            )
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Runtime configuration is invalid JSON: {source}"
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigurationError(
                "Runtime configuration root must be a JSON object."
            )
        return cls.from_mapping(payload)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self.values:
            raise ConfigurationError(
                f"Required runtime configuration key is missing: {key}"
            )
        return self.values[key]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "values": dict(self.values),
        }

    @property
    def configuration_sha256(self) -> str:
        return stable_sha256(self.to_dict())
