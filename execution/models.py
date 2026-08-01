from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping
import re

from kernel.exceptions import ConfigurationError, ValidationError
from kernel.serialization import normalize, stable_sha256


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


def _identifier(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{name} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{name} must not be empty.")
    if _IDENTIFIER.fullmatch(normalized) is None:
        raise ConfigurationError(
            f"{name} contains unsupported characters: {value!r}"
        )
    return normalized


def _timestamp(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be non-empty text.")
    text = value.strip()
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValidationError(
            f"{name} is not valid ISO-8601: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{name} must include a timezone.")
    return text


@dataclass(frozen=True)
class ExecutionRequest:
    schema_version: str
    execution_id: str
    plugin_id: str
    session_id: str
    payload: Any
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _identifier("schema_version", self.schema_version),
        )
        object.__setattr__(
            self,
            "execution_id",
            _identifier("execution_id", self.execution_id),
        )
        object.__setattr__(
            self,
            "plugin_id",
            _identifier("plugin_id", self.plugin_id),
        )
        object.__setattr__(
            self,
            "session_id",
            _identifier("session_id", self.session_id),
        )
        if not isinstance(self.metadata, Mapping):
            raise ConfigurationError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(normalize(dict(self.metadata))),
        )
        object.__setattr__(self, "payload", normalize(self.payload))

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        plugin_id: str,
        session_id: str,
        payload: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ExecutionRequest":
        return cls(
            schema_version="1.0",
            execution_id=execution_id,
            plugin_id=plugin_id,
            session_id=session_id,
            payload=payload,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "execution_id": self.execution_id,
            "plugin_id": self.plugin_id,
            "session_id": self.session_id,
            "payload": self.payload,
            "metadata": dict(self.metadata),
        }

    @property
    def request_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class ExecutionRecord:
    schema_version: str
    execution_id: str
    plugin_id: str
    session_id: str
    started_utc: str
    finished_utc: str
    elapsed_seconds: float
    success: bool
    request_sha256: str
    output_sha256: str | None
    error_type: str | None
    error_message: str | None

    def __post_init__(self) -> None:
        for name in ("execution_id", "plugin_id", "session_id"):
            object.__setattr__(
                self,
                name,
                _identifier(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "started_utc",
            _timestamp("started_utc", self.started_utc),
        )
        object.__setattr__(
            self,
            "finished_utc",
            _timestamp("finished_utc", self.finished_utc),
        )
        if isinstance(self.elapsed_seconds, bool):
            raise ValidationError(
                "elapsed_seconds must be a nonnegative number."
            )
        elapsed = float(self.elapsed_seconds)
        if elapsed < 0:
            raise ValidationError(
                "elapsed_seconds must be nonnegative."
            )
        object.__setattr__(self, "elapsed_seconds", elapsed)

        if not isinstance(self.success, bool):
            raise ValidationError("success must be boolean.")
        if self.success:
            if self.output_sha256 is None:
                raise ValidationError(
                    "Successful records require output_sha256."
                )
            if self.error_type is not None or self.error_message is not None:
                raise ValidationError(
                    "Successful records cannot contain error details."
                )
        else:
            if not self.error_type or not self.error_message:
                raise ValidationError(
                    "Failed records require error type and message."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "execution_id": self.execution_id,
            "plugin_id": self.plugin_id,
            "session_id": self.session_id,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "elapsed_seconds": self.elapsed_seconds,
            "success": self.success,
            "request_sha256": self.request_sha256,
            "output_sha256": self.output_sha256,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }

    @property
    def record_sha256(self) -> str:
        return stable_sha256(self.to_dict())
