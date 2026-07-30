# ============================================================
# PrimeAIExplorer v0.7
# Step 9 - Model Connector Foundation
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"

$ArchitectureDir = Join-Path $Root "architecture"
$SchemasDir      = Join-Path $Root "schemas"
$ConnectorsDir   = Join-Path $Root "connectors"
$CoreDir         = Join-Path $Root "core"
$TestsDir        = Join-Path $Root "tests"

$CanonicalConnectorPath = Join-Path $ArchitectureDir "Canonical_Connector.md"
$ConnectorSchemaPath    = Join-Path $SchemasDir "connector.schema.json"
$RegistryCsvPath        = Join-Path $ConnectorsDir "connector_registry.csv"
$RegistryJsonPath       = Join-Path $ConnectorsDir "connector_registry.json"

$ConnectorsInitPath     = Join-Path $ConnectorsDir "__init__.py"
$BaseConnectorPath      = Join-Path $ConnectorsDir "base.py"
$ConnectorModelsPath    = Join-Path $ConnectorsDir "models.py"
$MockConnectorPath      = Join-Path $ConnectorsDir "mock.py"

$ConnectorServicePath   = Join-Path $CoreDir "connector_service.py"
$ConnectorTestPath      = Join-Path $TestsDir "test_connector.py"

$CoreInitPath           = Join-Path $CoreDir "__init__.py"
$VersionPath            = Join-Path $Root "VERSION"
$ChangelogPath          = Join-Path $Root "CHANGELOG.md"

$RequiredDirectories = @(
    $ArchitectureDir,
    $SchemasDir,
    $ConnectorsDir,
    $CoreDir,
    $TestsDir
)

foreach ($Directory in $RequiredDirectories) {
    New-Item `
        -ItemType Directory `
        -Path $Directory `
        -Force | Out-Null
}

# ------------------------------------------------------------
# 1. Canonical Connector Specification
# ------------------------------------------------------------

$CanonicalConnector = @'
# PrimeAIExplorer Canonical Connector Specification

Version: 0.7.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical model-connector architecture for
PrimeAIExplorer.

A connector is a controlled scientific interface between an experiment and an
AI subject or deterministic baseline.

Experiments shall not communicate directly with model providers.

All model interactions shall pass through a registered connector implementing
the canonical interface.

---

## 2. Foundational Principle

The experiment defines the scientific task.

The connector transports that task to a subject.

The connector must not silently alter the scientific meaning of the
experiment.

Provider-specific transport behavior must remain separate from experiment
logic.

---

## 3. Canonical Connector Identifier

Every connector receives a permanent identifier:

CONNECTOR-NNNNNN

Examples:

- CONNECTOR-000001
- CONNECTOR-000002
- CONNECTOR-000125

Rules:

- Connector identifiers are permanent.
- Connector identifiers shall never be reused.
- Connector revisions use semantic versions.
- Materially different connector behavior requires a new version.
- Retired connectors remain preserved in the registry.

---

## 4. Connector Types

Supported connector types include:

- deterministic_mock
- local_model
- hosted_api
- command_line
- replay
- human_interface
- simulation

PrimeAIExplorer v0.7 implements a deterministic mock connector only.

No external model provider is contacted.

---

## 5. Connector Responsibilities

A connector is responsible for:

- validating requests
- preserving canonical messages
- mapping canonical roles to transport roles
- applying declared model parameters
- enforcing timeout policy
- collecting response evidence
- measuring latency
- recording provider metadata
- sanitizing secrets
- returning a canonical response object
- exposing connector capabilities

A connector is not responsible for:

- changing the experiment hypothesis
- selecting favorable outputs
- evaluating correctness
- calculating scientific statistics
- interpreting scientific meaning

---

## 6. Canonical Request

Every connector request shall contain:

- request ID
- connector ID
- connector version
- subject ID
- model identifier
- ordered messages
- generation parameters
- response-format request
- timeout
- metadata
- canonical request hash

Recommended request identifier:

REQUEST-NNNNNNNNNN

---

## 7. Canonical Message

Every message contains:

- role
- content
- optional name
- optional metadata

Permitted canonical roles include:

- system
- developer
- user
- assistant
- tool

Message order is scientifically significant and must be preserved.

---

## 8. Canonical Response

Every connector response shall contain:

- request ID
- connector ID
- connector version
- subject ID
- model identifier
- execution status
- raw text
- structured content when available
- finish reason
- refusal information
- usage
- timing
- provider metadata
- error information
- response hash

The response object records connector output.

It does not determine whether the answer is scientifically correct.

---

## 9. Execution Status

Permitted connector execution statuses include:

- succeeded
- failed
- timed_out
- refused
- invalid_request
- cancelled
- replayed

The connector must not report succeeded when no response was produced.

---

## 10. Capability Declaration

Every connector should declare capabilities such as:

- supports_system_messages
- supports_developer_messages
- supports_structured_output
- supports_seed
- supports_temperature
- supports_tools
- supports_streaming
- supports_usage_reporting
- supports_exact_model_revision
- maximum_context_tokens
- maximum_output_tokens

Unsupported capabilities must not be represented as controlled.

---

## 11. Deterministic Mock Connector

The deterministic mock connector supports free scientific pipeline validation.

It may operate in these modes:

- echo_last_user
- fixed_response
- deterministic_hash
- structured_prediction

Identical requests and identical connector configuration must produce identical
responses.

The mock connector must clearly identify itself as a deterministic baseline.

It must never be represented as evidence from a frontier model.

---

## 12. Echo Mode

Echo mode returns the content of the final user message.

This mode validates:

- message ordering
- request transport
- response capture
- hashing
- timing
- observation construction

---

## 13. Fixed-Response Mode

Fixed-response mode returns a configured immutable response.

This mode validates:

- exact-match evaluation
- structured-response parsing
- known-answer pipelines
- deterministic regression tests

---

## 14. Deterministic-Hash Mode

Deterministic-hash mode derives a response from the canonical request hash.

This mode validates:

- canonical serialization
- deterministic behavior
- cache keys
- reproducibility
- request identity

---

## 15. Structured-Prediction Mode

Structured-prediction mode returns a deterministic JSON object.

Potential fields include:

- prediction
- confidence
- abstain
- explanation
- connector_mode

This mode validates the complete structured-response pipeline without paid model
access.

---

## 16. Request Canonicalization

Request hashing shall use:

- UTF-8
- deterministic JSON key ordering
- deterministic message ordering
- explicit role labels
- normalized parameter representation
- no secret credentials
- no transient transport identifiers

SHA-256 is the default hashing algorithm.

---

## 17. Secret Protection

Connectors shall never persist:

- API keys
- access tokens
- authorization headers
- passwords
- session credentials
- private certificates

Sanitization occurs before request or error metadata enters the scientific
record.

---

## 18. Retry Policy

Retries shall be controlled by the execution layer rather than hidden inside a
connector unless explicitly documented.

Each retry must remain distinguishable as an execution attempt.

A connector must not silently replace an earlier failed response.

---

## 19. Timeout Policy

Timeout values shall be explicit.

A timeout response must report:

- timed_out status
- configured timeout
- elapsed duration
- partial output when safely available
- retry eligibility

PrimeAIExplorer v0.7 mock execution is synchronous and local.

---

## 20. Connector Registry

Every canonical connector shall appear in:

- connector_registry.csv
- connector_registry.json

Registry fields include:

- connector ID
- title
- short name
- version
- status
- connector type
- implementation module
- cost class
- external access
- created date
- modified date

---

## 21. Initial Connectors

PrimeAIExplorer v0.7 registers:

### CONNECTOR-000001 â€” Deterministic Mock Connector

Type:

deterministic_mock

External access:

false

Cost class:

free

Status:

Active

### CONNECTOR-000002 â€” Replay Connector

Type:

replay

External access:

false

Cost class:

free

Status:

Planned

### CONNECTOR-000003 â€” OpenAI Connector

Type:

hosted_api

External access:

true

Cost class:

paid

Status:

Disabled

The OpenAI connector is registered architecturally but is not implemented or
enabled in v0.7.

---

## 22. Connector Independence

Experiment code shall depend on the canonical connector interface rather than a
provider SDK.

This allows the same experiment to run against:

- mock subjects
- replayed observations
- local models
- hosted APIs
- future AI systems

Connector replacement should not require rewriting scientific experiment logic.

---

## 23. Observation Integration

A canonical connector response supplies evidence to the observation layer.

The observation layer records:

- connector ID
- connector version
- request hash
- response hash
- model identifier
- execution status
- latency
- usage
- raw text
- provider metadata
- sanitized errors

The connector does not write evaluation results.

---

## 24. Cache Integration

A connector request may contribute to a cache key.

Potential cache fields include:

- experiment version
- dataset checksum
- prompt hash
- connector ID
- connector version
- model identifier
- generation parameters
- response-format request

Cache reuse must remain transparent.

---

## 25. Testing Requirements

Every connector must pass:

- request validation tests
- deterministic behavior tests where applicable
- capability declaration tests
- message-order tests
- request-hash tests
- response-hash tests
- error-sanitization tests
- no-secret-persistence tests
- observation-integration tests

Hosted connectors additionally require network-failure and provider-error tests.

---

## 26. Free Development Policy

PrimeAIExplorer v0.7 performs no paid model calls.

The deterministic mock connector supports:

- full execution-path testing
- observation construction
- exact-match evaluation
- numeric evaluation
- structured-response validation
- statistical aggregation
- report generation

External connectors remain disabled until explicitly authorized.

---

## 27. Scientific Safeguards

PrimeAIExplorer connectors shall not:

- alter prompts silently
- hide provider adaptations
- store API keys
- fabricate usage data
- fabricate model revisions
- report mock output as frontier-model output
- retry invisibly
- discard failures
- select favorable responses
- perform scientific evaluation
- change experiment conditions
- claim network execution during local mock operation

---

## 28. Reproducibility Commitment

A connector execution is scientifically useful only when another researcher can
determine:

- which connector was used
- which connector version was used
- which messages were transported
- which parameters were requested
- which capabilities were supported
- whether external access occurred
- whether financial cost was possible
- which response was returned
- which hashes verify request and response integrity

PrimeAIExplorer shall preserve this information.

---

## 29. Guiding Statement

Connectors transport scientific tasks.

They do not define scientific conclusions.

Make observations first.

Evaluate transparently.

Summarize reproducibly.

Draw conclusions second.

---

End of Document
'@

Set-Content `
    -Path $CanonicalConnectorPath `
    -Value $CanonicalConnector `
    -Encoding UTF8

# ------------------------------------------------------------
# 2. Connector JSON Schema
# ------------------------------------------------------------

$ConnectorSchema = [ordered]@{
    '$schema' = "https://json-schema.org/draft/2020-12/schema"
    '$id' = "https://primenet.local/primeaiexplorer/schemas/connector.schema.json"
    title = "PrimeAIExplorer Canonical Connector Definition"
    description = "Canonical schema for a PrimeAIExplorer connector definition."
    type = "object"
    additionalProperties = $false

    required = @(
        "connector_id",
        "connector_schema_version",
        "title",
        "short_name",
        "version",
        "status",
        "connector_type",
        "implementation_module",
        "external_access",
        "cost_class",
        "capabilities"
    )

    properties = [ordered]@{
        connector_id = [ordered]@{
            type = "string"
            pattern = "^CONNECTOR-[0-9]{6}$"
        }

        connector_schema_version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        title = [ordered]@{
            type = "string"
            minLength = 1
        }

        short_name = [ordered]@{
            type = "string"
            pattern = "^[a-z][a-z0-9_]*$"
        }

        version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        status = [ordered]@{
            type = "string"
            enum = @(
                "Planned",
                "Draft",
                "Active",
                "Disabled",
                "Suspended",
                "Retired",
                "Invalidated"
            )
        }

        connector_type = [ordered]@{
            type = "string"
            enum = @(
                "deterministic_mock",
                "local_model",
                "hosted_api",
                "command_line",
                "replay",
                "human_interface",
                "simulation"
            )
        }

        implementation_module = [ordered]@{
            type = @("string", "null")
        }

        external_access = [ordered]@{
            type = "boolean"
        }

        cost_class = [ordered]@{
            type = "string"
            enum = @(
                "free",
                "local_resource",
                "paid",
                "unknown"
            )
        }

        capabilities = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "supports_system_messages",
                "supports_structured_output",
                "supports_seed",
                "supports_temperature",
                "supports_tools",
                "supports_streaming",
                "supports_usage_reporting"
            )
            properties = [ordered]@{
                supports_system_messages = [ordered]@{
                    type = "boolean"
                }
                supports_developer_messages = [ordered]@{
                    type = "boolean"
                }
                supports_structured_output = [ordered]@{
                    type = "boolean"
                }
                supports_seed = [ordered]@{
                    type = "boolean"
                }
                supports_temperature = [ordered]@{
                    type = "boolean"
                }
                supports_tools = [ordered]@{
                    type = "boolean"
                }
                supports_streaming = [ordered]@{
                    type = "boolean"
                }
                supports_usage_reporting = [ordered]@{
                    type = "boolean"
                }
                maximum_context_tokens = [ordered]@{
                    type = @("integer", "null")
                    minimum = 1
                }
                maximum_output_tokens = [ordered]@{
                    type = @("integer", "null")
                    minimum = 1
                }
            }
        }
    }
}

$ConnectorSchema |
    ConvertTo-Json -Depth 30 |
    Set-Content `
        -Path $ConnectorSchemaPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 3. Connector Registry
# ------------------------------------------------------------

$RegistryRows = @(
    [pscustomobject][ordered]@{
        connector_id          = "CONNECTOR-000001"
        title                 = "Deterministic Mock Connector"
        short_name            = "deterministic_mock"
        version               = "0.1.0"
        status                = "Active"
        connector_type        = "deterministic_mock"
        implementation_module = "connectors.mock"
        cost_class            = "free"
        external_access       = "false"
        created_date          = "2026-07-25"
        modified_date         = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        connector_id          = "CONNECTOR-000002"
        title                 = "Replay Connector"
        short_name            = "replay"
        version               = "0.1.0"
        status                = "Planned"
        connector_type        = "replay"
        implementation_module = ""
        cost_class            = "free"
        external_access       = "false"
        created_date          = "2026-07-25"
        modified_date         = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        connector_id          = "CONNECTOR-000003"
        title                 = "OpenAI Connector"
        short_name            = "openai"
        version               = "0.1.0"
        status                = "Disabled"
        connector_type        = "hosted_api"
        implementation_module = ""
        cost_class            = "paid"
        external_access       = "true"
        created_date          = "2026-07-25"
        modified_date         = "2026-07-25"
    }
)

$RegistryRows |
    Export-Csv `
        -Path $RegistryCsvPath `
        -NoTypeInformation `
        -Encoding UTF8

$RegistryObject = [ordered]@{
    registry_name = "PrimeAIExplorer Connector Registry"
    registry_version = "0.7.0"
    connector_schema_version = "0.7.0"
    updated_date = "2026-07-25"
    connectors = @(
        foreach ($Row in $RegistryRows) {
            [ordered]@{
                connector_id          = $Row.connector_id
                title                 = $Row.title
                short_name            = $Row.short_name
                version               = $Row.version
                status                = $Row.status
                connector_type        = $Row.connector_type
                implementation_module = $(
                    if ($Row.implementation_module) {
                        $Row.implementation_module
                    }
                    else {
                        $null
                    }
                )
                cost_class            = $Row.cost_class
                external_access       = $(
                    $Row.external_access -eq "true"
                )
                created_date          = $Row.created_date
                modified_date         = $Row.modified_date
            }
        }
    )
}

$RegistryObject |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -Path $RegistryJsonPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 4. Python Connector Models
# ------------------------------------------------------------

$ConnectorModels = @'
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
'@

Set-Content `
    -Path $ConnectorModelsPath `
    -Value $ConnectorModels `
    -Encoding UTF8

# ------------------------------------------------------------
# 5. Base Connector Interface
# ------------------------------------------------------------

$BaseConnector = @'
"""Abstract model-independent connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from connectors.models import ConnectorRequest, ConnectorResponse


@dataclass(frozen=True, slots=True)
class ConnectorCapabilities:
    supports_system_messages: bool
    supports_developer_messages: bool
    supports_structured_output: bool
    supports_seed: bool
    supports_temperature: bool
    supports_tools: bool
    supports_streaming: bool
    supports_usage_reporting: bool
    supports_exact_model_revision: bool
    maximum_context_tokens: int | None = None
    maximum_output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "supports_system_messages": self.supports_system_messages,
            "supports_developer_messages": (
                self.supports_developer_messages
            ),
            "supports_structured_output": (
                self.supports_structured_output
            ),
            "supports_seed": self.supports_seed,
            "supports_temperature": self.supports_temperature,
            "supports_tools": self.supports_tools,
            "supports_streaming": self.supports_streaming,
            "supports_usage_reporting": (
                self.supports_usage_reporting
            ),
            "supports_exact_model_revision": (
                self.supports_exact_model_revision
            ),
            "maximum_context_tokens": self.maximum_context_tokens,
            "maximum_output_tokens": self.maximum_output_tokens,
        }


class BaseConnector(ABC):
    """Canonical connector interface."""

    connector_id: str
    connector_version: str
    title: str
    connector_type: str
    external_access: bool
    cost_class: str

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """Return declared connector capabilities."""

    @abstractmethod
    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        """Execute one canonical connector request."""

    def validate_request(
        self,
        request: ConnectorRequest,
    ) -> None:
        """Validate connector ownership and basic capabilities."""

        if request.connector_id != self.connector_id:
            raise ValueError(
                "Request connector ID does not match connector instance."
            )

        if request.connector_version != self.connector_version:
            raise ValueError(
                "Request connector version does not match connector instance."
            )

        has_system = any(
            message.role.value == "system"
            for message in request.messages
        )

        if has_system and not self.capabilities.supports_system_messages:
            raise ValueError(
                "Connector does not support system messages."
            )


__all__ = [
    "BaseConnector",
    "ConnectorCapabilities",
]
'@

Set-Content `
    -Path $BaseConnectorPath `
    -Value $BaseConnector `
    -Encoding UTF8

# ------------------------------------------------------------
# 6. Deterministic Mock Connector
# ------------------------------------------------------------

$MockConnector = @'
"""Deterministic free connector for PrimeAIExplorer pipeline validation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
import json
import time
from typing import Any

from connectors.base import BaseConnector, ConnectorCapabilities
from connectors.models import (
    ConnectorError,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorTiming,
    ConnectorUsage,
    MessageRole,
    canonical_json,
    sha256_text,
)


class MockMode(StrEnum):
    ECHO_LAST_USER = "echo_last_user"
    FIXED_RESPONSE = "fixed_response"
    DETERMINISTIC_HASH = "deterministic_hash"
    STRUCTURED_PREDICTION = "structured_prediction"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DeterministicMockConnector(BaseConnector):
    connector_id = "CONNECTOR-000001"
    connector_version = "0.1.0"
    title = "Deterministic Mock Connector"
    connector_type = "deterministic_mock"
    external_access = False
    cost_class = "free"

    def __init__(
        self,
        *,
        mode: MockMode = MockMode.ECHO_LAST_USER,
        fixed_response: str = "",
    ) -> None:
        self.mode = MockMode(mode)
        self.fixed_response = fixed_response

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_system_messages=True,
            supports_developer_messages=True,
            supports_structured_output=True,
            supports_seed=True,
            supports_temperature=False,
            supports_tools=False,
            supports_streaming=False,
            supports_usage_reporting=True,
            supports_exact_model_revision=True,
            maximum_context_tokens=1_000_000,
            maximum_output_tokens=100_000,
        )

    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        self.validate_request(request)

        started_at = utc_now_iso()
        start_clock = time.perf_counter()

        try:
            raw_text = self._generate_response(request)
            status = ConnectorStatus.SUCCEEDED
            finish_reason = "completed"
            refusal = None
            error = ConnectorError()
        except Exception as exception:
            raw_text = None
            status = ConnectorStatus.FAILED
            finish_reason = "error"
            refusal = None
            error = ConnectorError(
                category="mock_connector_error",
                message=str(exception),
                retryable=False,
            )

        latency = time.perf_counter() - start_clock
        completed_at = utc_now_iso()

        input_characters = sum(
            len(message.content)
            for message in request.messages
        )
        output_characters = len(raw_text or "")

        response_hash = (
            sha256_text(raw_text)
            if raw_text is not None
            else None
        )

        return ConnectorResponse(
            request_id=request.request_id,
            connector_id=self.connector_id,
            connector_version=self.connector_version,
            subject_id=request.subject_id,
            model_identifier=request.model_identifier,
            status=status,
            raw_text=raw_text,
            finish_reason=finish_reason,
            refusal=refusal,
            usage=ConnectorUsage(
                input_characters=input_characters,
                output_characters=output_characters,
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                usage_source="local_character_count",
            ),
            timing=ConnectorTiming(
                latency_seconds=latency,
                started_at_utc=started_at,
                completed_at_utc=completed_at,
            ),
            provider_metadata={
                "provider": "PrimeAIExplorer",
                "connector_mode": self.mode.value,
                "external_access": False,
                "cost_incurred": False,
                "deterministic_baseline": True,
            },
            error=error,
            request_sha256=request.request_sha256,
            response_sha256=response_hash,
        )

    def _generate_response(
        self,
        request: ConnectorRequest,
    ) -> str:
        if self.mode is MockMode.ECHO_LAST_USER:
            return self._last_user_content(request)

        if self.mode is MockMode.FIXED_RESPONSE:
            return self.fixed_response

        if self.mode is MockMode.DETERMINISTIC_HASH:
            return json.dumps(
                {
                    "request_sha256": request.request_sha256,
                    "connector_mode": self.mode.value,
                    "deterministic": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        if self.mode is MockMode.STRUCTURED_PREDICTION:
            user_content = self._last_user_content(request)
            digest = sha256_text(user_content)
            prediction = int(digest[:8], 16) % 1000

            return json.dumps(
                {
                    "prediction": prediction,
                    "confidence": 1.0,
                    "abstain": False,
                    "explanation": (
                        "Deterministic mock prediction derived from "
                        "the SHA-256 hash of the final user message."
                    ),
                    "connector_mode": self.mode.value,
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        raise RuntimeError(f"Unsupported mock mode: {self.mode}")

    @staticmethod
    def _last_user_content(
        request: ConnectorRequest,
    ) -> str:
        for message in reversed(request.messages):
            if message.role is MessageRole.USER:
                return message.content

        raise ValueError(
            "Echo and structured mock modes require a user message."
        )


__all__ = [
    "DeterministicMockConnector",
    "MockMode",
]
'@

Set-Content `
    -Path $MockConnectorPath `
    -Value $MockConnector `
    -Encoding UTF8

# ------------------------------------------------------------
# 7. Connector Package Initialization
# ------------------------------------------------------------

$ConnectorsInit = @'
"""PrimeAIExplorer model-independent connector package."""

from connectors.base import BaseConnector, ConnectorCapabilities
from connectors.mock import DeterministicMockConnector, MockMode
from connectors.models import (
    ConnectorError,
    ConnectorMessage,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorTiming,
    ConnectorUsage,
    MessageRole,
    canonical_request_id,
)


__all__ = [
    "BaseConnector",
    "ConnectorCapabilities",
    "ConnectorError",
    "ConnectorMessage",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorStatus",
    "ConnectorTiming",
    "ConnectorUsage",
    "DeterministicMockConnector",
    "MessageRole",
    "MockMode",
    "canonical_request_id",
]
'@

Set-Content `
    -Path $ConnectorsInitPath `
    -Value $ConnectorsInit `
    -Encoding UTF8

# ------------------------------------------------------------
# 8. Connector Service
# ------------------------------------------------------------

$ConnectorService = @'
"""Connector registration and model-independent execution service."""

from __future__ import annotations

from dataclasses import dataclass, field

from connectors.base import BaseConnector
from connectors.models import ConnectorRequest, ConnectorResponse


@dataclass(slots=True)
class ConnectorService:
    """In-memory connector registry and execution service."""

    _connectors: dict[str, BaseConnector] = field(default_factory=dict)

    def register(
        self,
        connector: BaseConnector,
        *,
        replace: bool = False,
    ) -> None:
        connector_id = connector.connector_id

        if connector_id in self._connectors and not replace:
            raise ValueError(
                f"Connector already registered: {connector_id}"
            )

        self._connectors[connector_id] = connector

    def get(self, connector_id: str) -> BaseConnector:
        try:
            return self._connectors[connector_id]
        except KeyError as error:
            raise KeyError(
                f"Connector is not registered: {connector_id}"
            ) from error

    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        connector = self.get(request.connector_id)
        return connector.execute(request)

    def registered_connector_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._connectors))


__all__ = ["ConnectorService"]
'@

Set-Content `
    -Path $ConnectorServicePath `
    -Value $ConnectorService `
    -Encoding UTF8

if (-not (Test-Path $CoreInitPath)) {
    Set-Content `
        -Path $CoreInitPath `
        -Value '"""PrimeAIExplorer core package."""' `
        -Encoding UTF8
}

# ------------------------------------------------------------
# 9. Unit Tests
# ------------------------------------------------------------

$ConnectorTests = @'
"""Tests for PrimeAIExplorer v0.7 connector foundation."""

from __future__ import annotations

import json
import unittest

from connectors import (
    ConnectorMessage,
    ConnectorRequest,
    ConnectorStatus,
    DeterministicMockConnector,
    MessageRole,
    MockMode,
    canonical_request_id,
)
from core.connector_service import ConnectorService


def build_request(
    *,
    sequence: int = 1,
    user_content: str = "Prime gaps: 2, 4, 2, 4",
) -> ConnectorRequest:
    return ConnectorRequest(
        request_id=canonical_request_id(sequence),
        connector_id="CONNECTOR-000001",
        connector_version="0.1.0",
        subject_id="SUBJECT-000001",
        model_identifier="deterministic-mock",
        messages=(
            ConnectorMessage(
                role=MessageRole.SYSTEM,
                content="Return a deterministic response.",
            ),
            ConnectorMessage(
                role=MessageRole.USER,
                content=user_content,
            ),
        ),
        parameters={
            "seed": 20260725,
        },
        response_format={
            "type": "text",
        },
        timeout_seconds=30.0,
        metadata={
            "experiment_id": "EXP-000001",
        },
    )


class RequestIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_request_id(1),
            "REQUEST-0000000001",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_request_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_request_id(True)


class ConnectorRequestTests(unittest.TestCase):
    def test_request_hash_is_stable(self) -> None:
        first = build_request()
        second = build_request()

        self.assertEqual(
            first.request_sha256,
            second.request_sha256,
        )
        self.assertEqual(len(first.request_sha256), 64)

    def test_empty_message_list_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConnectorRequest(
                request_id="REQUEST-0000000001",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                messages=(),
            )

    def test_nonpositive_timeout_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConnectorRequest(
                request_id="REQUEST-0000000001",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                messages=(
                    ConnectorMessage(
                        role=MessageRole.USER,
                        content="Test",
                    ),
                ),
                timeout_seconds=0,
            )


class MockConnectorTests(unittest.TestCase):
    def test_echo_last_user(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.ECHO_LAST_USER,
        )
        response = connector.execute(build_request())

        self.assertEqual(
            response.status,
            ConnectorStatus.SUCCEEDED,
        )
        self.assertEqual(
            response.raw_text,
            "Prime gaps: 2, 4, 2, 4",
        )
        self.assertFalse(
            response.provider_metadata["external_access"]
        )
        self.assertFalse(
            response.provider_metadata["cost_incurred"]
        )

    def test_fixed_response(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.FIXED_RESPONSE,
            fixed_response='{"prediction": 6}',
        )
        response = connector.execute(build_request())

        self.assertEqual(
            response.raw_text,
            '{"prediction": 6}',
        )

    def test_hash_response_is_deterministic(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.DETERMINISTIC_HASH,
        )

        first = connector.execute(build_request())
        second = connector.execute(build_request())

        self.assertEqual(first.raw_text, second.raw_text)
        self.assertEqual(
            first.response_sha256,
            second.response_sha256,
        )

        payload = json.loads(first.raw_text)

        self.assertEqual(
            payload["request_sha256"],
            build_request().request_sha256,
        )
        self.assertTrue(payload["deterministic"])

    def test_structured_prediction(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION,
        )
        response = connector.execute(build_request())
        payload = json.loads(response.raw_text)

        self.assertIn("prediction", payload)
        self.assertIn("confidence", payload)
        self.assertFalse(payload["abstain"])
        self.assertEqual(
            payload["connector_mode"],
            "structured_prediction",
        )

    def test_different_input_changes_prediction(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION,
        )

        first = json.loads(
            connector.execute(
                build_request(user_content="Input A")
            ).raw_text
        )
        second = json.loads(
            connector.execute(
                build_request(user_content="Input B")
            ).raw_text
        )

        self.assertNotEqual(
            first["prediction"],
            second["prediction"],
        )

    def test_request_connector_mismatch_rejected(self) -> None:
        connector = DeterministicMockConnector()

        request = ConnectorRequest(
            request_id="REQUEST-0000000001",
            connector_id="CONNECTOR-999999",
            connector_version="0.1.0",
            subject_id="SUBJECT-000001",
            model_identifier="deterministic-mock",
            messages=(
                ConnectorMessage(
                    role=MessageRole.USER,
                    content="Test",
                ),
            ),
        )

        with self.assertRaises(ValueError):
            connector.execute(request)

    def test_usage_is_local_measurement(self) -> None:
        connector = DeterministicMockConnector()
        response = connector.execute(build_request())

        self.assertEqual(
            response.usage.usage_source,
            "local_character_count",
        )
        self.assertIsNone(response.usage.total_tokens)

    def test_capabilities(self) -> None:
        connector = DeterministicMockConnector()
        capabilities = connector.capabilities

        self.assertTrue(
            capabilities.supports_system_messages
        )
        self.assertTrue(
            capabilities.supports_structured_output
        )
        self.assertFalse(capabilities.supports_tools)
        self.assertFalse(connector.external_access)
        self.assertEqual(connector.cost_class, "free")


class ConnectorServiceTests(unittest.TestCase):
    def test_register_and_execute(self) -> None:
        service = ConnectorService()
        service.register(
            DeterministicMockConnector(
                mode=MockMode.ECHO_LAST_USER,
            )
        )

        response = service.execute(build_request())

        self.assertEqual(
            response.status,
            ConnectorStatus.SUCCEEDED,
        )

    def test_duplicate_registration_rejected(self) -> None:
        service = ConnectorService()
        service.register(DeterministicMockConnector())

        with self.assertRaises(ValueError):
            service.register(DeterministicMockConnector())

    def test_missing_connector_rejected(self) -> None:
        service = ConnectorService()

        with self.assertRaises(KeyError):
            service.get("CONNECTOR-000001")

    def test_registered_ids_are_sorted(self) -> None:
        service = ConnectorService()
        service.register(DeterministicMockConnector())

        self.assertEqual(
            service.registered_connector_ids(),
            ("CONNECTOR-000001",),
        )


if __name__ == "__main__":
    unittest.main()
'@

Set-Content `
    -Path $ConnectorTestPath `
    -Value $ConnectorTests `
    -Encoding UTF8

# ------------------------------------------------------------
# 10. Version and Changelog
# ------------------------------------------------------------

Set-Content `
    -Path $VersionPath `
    -Value "0.7.0" `
    -Encoding UTF8

$NewChangelogSection = @'
## 0.7.0 - 2026-07-25

### Added

- Canonical Connector Specification.
- Canonical connector-definition JSON Schema.
- Connector registry in CSV and JSON.
- Model-independent connector interface.
- Canonical connector request and response models.
- Canonical request identifiers.
- Deterministic request and response hashing.
- Connector capability declarations.
- Deterministic mock connector.
- Echo, fixed-response, deterministic-hash, and structured-prediction modes.
- Connector registration and execution service.
- Local usage and latency capture.
- Connector unit tests.

### Scientific policy

Experiments communicate with AI subjects only through canonical connectors.

The deterministic mock connector performs no external access and incurs no
financial cost.

Mock responses must never be represented as frontier-model evidence.

Provider-specific connector behavior remains separate from scientific
experiment logic.

'@

$ExistingChangelog = ""

if (Test-Path $ChangelogPath) {
    $ExistingChangelog = Get-Content $ChangelogPath -Raw
}

if ($ExistingChangelog -match "(?m)^# PrimeAIExplorer Changelog") {
    $ExistingBody = $ExistingChangelog -replace `
        "(?m)^# PrimeAIExplorer Changelog\s*", ""
}
else {
    $ExistingBody = $ExistingChangelog
}

if ($ExistingBody -notmatch "(?m)^## 0\.7\.0 - 2026-07-25") {
    $UpdatedChangelog = @"
# PrimeAIExplorer Changelog

$NewChangelogSection$ExistingBody
"@

    Set-Content `
        -Path $ChangelogPath `
        -Value $UpdatedChangelog.TrimEnd() `
        -Encoding UTF8
}

# ------------------------------------------------------------
# 11. Validation
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.7"
Write-Host " Model Connector Foundation"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

$RequiredFiles = @(
    $CanonicalConnectorPath,
    $ConnectorSchemaPath,
    $RegistryCsvPath,
    $RegistryJsonPath,
    $ConnectorsInitPath,
    $BaseConnectorPath,
    $ConnectorModelsPath,
    $MockConnectorPath,
    $ConnectorServicePath,
    $ConnectorTestPath,
    $VersionPath,
    $ChangelogPath
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        Write-Host "[FAIL] Missing file: $File"
        $Failed = $true
        continue
    }

    $Item = Get-Item $File

    if ($Item.Length -le 0) {
        Write-Host "[FAIL] Empty file: $File"
        $Failed = $true
        continue
    }

    Write-Host "[PASS] $($Item.FullName)"
    Write-Host "       Size: $($Item.Length) bytes"
}

$RequiredPhrases = @(
    "PrimeAIExplorer Canonical Connector Specification",
    "CONNECTOR-NNNNNN",
    "The experiment defines the scientific task.",
    "Deterministic Mock Connector",
    "Connector Independence",
    "PrimeAIExplorer v0.7 performs no paid model calls.",
    "Connectors transport scientific tasks.",
    "They do not define scientific conclusions.",
    "Draw conclusions second."
)

$DocumentContent = Get-Content $CanonicalConnectorPath -Raw

foreach ($Phrase in $RequiredPhrases) {
    if ($DocumentContent.Contains($Phrase)) {
        Write-Host "[PASS] Found: $Phrase"
    }
    else {
        Write-Host "[FAIL] Missing phrase: $Phrase"
        $Failed = $true
    }
}

try {
    $Schema = Get-Content $ConnectorSchemaPath -Raw |
        ConvertFrom-Json

    if (
        $Schema.title -eq
        "PrimeAIExplorer Canonical Connector Definition"
    ) {
        Write-Host "[PASS] Connector schema JSON is valid"
    }
    else {
        Write-Host "[FAIL] Unexpected connector schema title"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Connector schema JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

try {
    $RegistryJson = Get-Content $RegistryJsonPath -Raw |
        ConvertFrom-Json

    if ($RegistryJson.connectors.Count -eq 3) {
        Write-Host "[PASS] Connector registry contains 3 connectors"
    }
    else {
        Write-Host "[FAIL] Unexpected connector count"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Connector registry JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

$CsvRows = @(
    Import-Csv $RegistryCsvPath
)

if ($CsvRows.Count -eq 3) {
    Write-Host "[PASS] Connector registry CSV contains 3 connectors"
}
else {
    Write-Host "[FAIL] Unexpected connector CSV count"
    $Failed = $true
}

$DuplicateIds = @(
    $CsvRows |
        Group-Object connector_id |
        Where-Object Count -gt 1
)

if ($DuplicateIds.Count -eq 0) {
    Write-Host "[PASS] No duplicate connector identifiers"
}
else {
    Write-Host "[FAIL] Duplicate connector identifiers"
    $Failed = $true
}

$InvalidIds = @(
    $CsvRows |
        Where-Object {
            $_.connector_id -notmatch "^CONNECTOR-[0-9]{6}$"
        }
)

if ($InvalidIds.Count -eq 0) {
    Write-Host "[PASS] All connector identifiers are canonical"
}
else {
    Write-Host "[FAIL] Invalid connector identifiers"
    $Failed = $true
}

$MockRow = $CsvRows |
    Where-Object connector_id -eq "CONNECTOR-000001"

if (
    $MockRow.external_access -eq "false" -and
    $MockRow.cost_class -eq "free"
) {
    Write-Host "[PASS] Mock connector is local and free"
}
else {
    Write-Host "[FAIL] Mock connector governance is incorrect"
    $Failed = $true
}

$OpenAIRow = $CsvRows |
    Where-Object connector_id -eq "CONNECTOR-000003"

if (
    $OpenAIRow.status -eq "Disabled" -and
    $OpenAIRow.cost_class -eq "paid"
) {
    Write-Host "[PASS] Hosted paid connector remains disabled"
}
else {
    Write-Host "[FAIL] Hosted connector governance is incorrect"
    $Failed = $true
}

$Version = (Get-Content $VersionPath -Raw).Trim()

if ($Version -eq "0.7.0") {
    Write-Host "[PASS] VERSION is 0.7.0"
}
else {
    Write-Host "[FAIL] VERSION is not 0.7.0"
    $Failed = $true
}

Write-Host ""
Write-Host "Connector registry:"

$CsvRows |
    Format-Table `
        connector_id,
        title,
        version,
        status,
        connector_type,
        cost_class,
        external_access `
        -AutoSize

Write-Host ""
Write-Host "Python compilation:"

Push-Location $Root

try {
    py -m compileall `
        .\connectors `
        .\core `
        .\tests

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Python compilation failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Python compilation completed"
    }

    Write-Host ""
    Write-Host "Connector tests:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_connector.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Connector tests failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Connector tests passed"
    }

    Write-Host ""
    Write-Host "Full test suite:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_*.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Full test suite failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Full test suite passed"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Canonical connector document line count:"

$LineCount = (Get-Content $CanonicalConnectorPath).Count
Write-Host $LineCount

if ($LineCount -lt 250) {
    Write-Host "[WARN] Canonical connector document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "PRIMEAIEXPLORER v0.7 FAILED"
    exit 1
}

Write-Host ""
Write-Host "PRIMEAIEXPLORER v0.7 PASSED"
