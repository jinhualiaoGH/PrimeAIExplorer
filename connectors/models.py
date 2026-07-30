"""Canonical request and response models for PrimeAIExplorer connectors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


CONNECTOR_SCHEMA_VERSION = "0.7.0"


class MessageRole(StrEnum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConnectorStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    REFUSED = "refused"
    INVALID_REQUEST = "invalid_request"
    CANCELLED = "cancelled"
    REPLAYED = "replayed"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def canonical_request_id(sequence: int) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Request sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Request sequence must be between 1 and 9,999,999,999."
        )

    return f"REQUEST-{sequence:010d}"


@dataclass(frozen=True, slots=True)
class ConnectorMessage:
    role: MessageRole
    content: str
    name: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("Message content must be a string.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "name": self.name,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    request_id: str
    connector_id: str
    connector_version: str
    subject_id: str
    model_identifier: str
    messages: Sequence[ConnectorMessage]
    parameters: Mapping[str, Any] = field(default_factory=dict)
    response_format: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 120.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError(
                "A connector request must contain at least one message."
            )

        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be greater than zero.")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "connector_version": self.connector_version,
            "subject_id": self.subject_id,
            "model_identifier": self.model_identifier,
            "messages": [
                message.to_dict()
                for message in self.messages
            ],
            "parameters": dict(self.parameters),
            "response_format": dict(self.response_format),
            "timeout_seconds": self.timeout_seconds,
            "metadata": dict(self.metadata),
        }

    @property
    def request_sha256(self) -> str:
        return sha256_text(
            canonical_json(self.canonical_payload())
        )


@dataclass(frozen=True, slots=True)
class ConnectorUsage:
    input_characters: int
    output_characters: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    usage_source: str = "local_measurement"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectorTiming:
    latency_seconds: float
    started_at_utc: str
    completed_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectorError:
    category: str | None = None
    message: str | None = None
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectorResponse:
    request_id: str
    connector_id: str
    connector_version: str
    subject_id: str
    model_identifier: str
    status: ConnectorStatus
    raw_text: str | None
    finish_reason: str | None
    refusal: str | None
    usage: ConnectorUsage
    timing: ConnectorTiming
    provider_metadata: Mapping[str, Any]
    error: ConnectorError
    request_sha256: str
    response_sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "connector_version": self.connector_version,
            "subject_id": self.subject_id,
            "model_identifier": self.model_identifier,
            "status": self.status.value,
            "raw_text": self.raw_text,
            "finish_reason": self.finish_reason,
            "refusal": self.refusal,
            "usage": self.usage.to_dict(),
            "timing": self.timing.to_dict(),
            "provider_metadata": dict(self.provider_metadata),
            "error": self.error.to_dict(),
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
        }


__all__ = [
    "CONNECTOR_SCHEMA_VERSION",
    "ConnectorError",
    "ConnectorMessage",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorStatus",
    "ConnectorTiming",
    "ConnectorUsage",
    "MessageRole",
    "canonical_json",
    "canonical_request_id",
    "sha256_text",
]
