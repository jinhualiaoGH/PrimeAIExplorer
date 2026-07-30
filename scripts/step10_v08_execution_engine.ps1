# ============================================================
# PrimeAIExplorer v0.8
# Step 10 - Deterministic Execution Engine
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"

$ArchitectureDir = Join-Path $Root "architecture"
$SchemasDir      = Join-Path $Root "schemas"
$ExecutionsDir   = Join-Path $Root "executions"
$CoreDir         = Join-Path $Root "core"
$TestsDir        = Join-Path $Root "tests"
$ExamplesDir     = Join-Path $Root "examples"
$ResultsDir      = Join-Path $Root "results"

$CanonicalExecutionPath = Join-Path $ArchitectureDir "Canonical_Execution.md"
$RunManifestSchemaPath  = Join-Path $SchemasDir "run_manifest.schema.json"

$RunRegistryCsvPath     = Join-Path $ExecutionsDir "run_registry.csv"
$RunRegistryJsonPath    = Join-Path $ExecutionsDir "run_registry.json"

$ExecutionContextPath   = Join-Path $CoreDir "execution_context.py"
$RegistryLoaderPath     = Join-Path $CoreDir "registry_loader.py"
$ExecutionEnginePath    = Join-Path $CoreDir "execution_engine.py"

$ExecutionTestPath      = Join-Path $TestsDir "test_execution_engine.py"
$DemoPath               = Join-Path $ExamplesDir "run_v08_demo.py"

$VersionPath            = Join-Path $Root "VERSION"
$ChangelogPath          = Join-Path $Root "CHANGELOG.md"

$RequiredDirectories = @(
    $ArchitectureDir,
    $SchemasDir,
    $ExecutionsDir,
    $CoreDir,
    $TestsDir,
    $ExamplesDir,
    $ResultsDir
)

foreach ($Directory in $RequiredDirectories) {
    New-Item `
        -ItemType Directory `
        -Path $Directory `
        -Force | Out-Null
}

# ------------------------------------------------------------
# 1. Canonical Execution Specification
# ------------------------------------------------------------

$CanonicalExecution = @'
# PrimeAIExplorer Canonical Execution Specification

Version: 0.8.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical execution architecture of
PrimeAIExplorer.

The execution engine coordinates a scientific experiment from validated
configuration through permanent artifacts.

It does not redefine experiments, datasets, prompts, evaluations, statistics,
or reports.

It executes their declared relationships under a controlled protocol.

---

## 2. Foundational Principle

A scientific run must preserve both what was planned and what actually
occurred.

The execution engine shall therefore preserve:

- run configuration
- registry versions
- execution phases
- connector requests
- connector responses
- observations
- evaluations
- summaries
- reports
- failures
- timing
- integrity hashes

Successful outputs alone are not a complete scientific record.

---

## 3. Canonical Run Identifier

Every execution run receives a permanent identifier:

RUN-YYYYMMDD-NNNNNN

Examples:

- RUN-20260725-000001
- RUN-20260725-000002
- RUN-20270101-000001

Rules:

- Run identifiers are permanent.
- Run identifiers shall never be reused.
- A rerun receives a new run identifier.
- Run sequence allocation must eventually be atomic.
- Run identity shall not depend only on a directory name.

---

## 4. Run Lifecycle

Permitted run statuses include:

- planned
- validating
- ready
- running
- completed
- completed_with_failures
- failed
- cancelled
- superseded

### planned

The run has been defined but not validated.

### validating

Registry and configuration validation is in progress.

### ready

All pre-execution validation checks passed.

### running

One or more scientific cases are executing.

### completed

All planned cases completed successfully.

### completed_with_failures

The run completed, but one or more cases failed or were invalid.

### failed

A run-level failure prevented completion.

### cancelled

Execution was intentionally stopped.

### superseded

The original run remains preserved but a replacement run is identified.

---

## 5. Execution Phases

The canonical initial phases are:

1. initialize
2. load_registries
3. validate
4. prepare_cases
5. execute
6. preserve_observations
7. evaluate
8. summarize
9. report
10. finalize

Every phase should record:

- phase name
- status
- start timestamp
- completion timestamp
- duration
- message
- artifact references
- error details

---

## 6. Execution Context

Every run receives an immutable execution context.

The context should include:

- run ID
- run schema version
- PrimeAIExplorer version
- experiment ID and version
- dataset ID and version
- prompt ID and version
- connector ID and version
- subject ID
- model identifier
- random seed
- execution mode
- output directory
- creation timestamp
- environment summary

The context is not a container for mutable run results.

---

## 7. Registry Loading

The execution engine shall load scientific objects from canonical registries.

Initial registries include:

- experiment registry
- dataset registry
- prompt registry
- connector registry
- evaluation registry
- report registry
- statistics registry when present

Registry loading shall validate:

- file existence
- parseability
- unique identifiers
- identifier format
- requested object existence
- compatible relationships

Hard-coded scientific relationships should be minimized.

---

## 8. Relationship Validation

Before execution, the engine should verify:

- the prompt references the selected experiment
- the prompt references the selected dataset
- the connector is registered
- the connector is active
- disabled connectors cannot execute
- paid connectors require explicit authorization
- external access is false in free mode
- experiment, dataset, and prompt versions are known
- the subject and model identifiers are declared

Execution must fail before model access when governance checks fail.

---

## 9. Free-Mode Governance

PrimeAIExplorer v0.8 runs in free deterministic mode.

The execution engine shall permit only connectors satisfying:

- external access is false
- cost class is free
- status is Active
- deterministic baseline is declared

The OpenAI connector remains disabled.

No API key is required.

No network request is performed.

No financial cost is incurred.

---

## 10. Scientific Cases

A run contains one or more scientific cases.

Each case should define:

- case ID
- condition ID
- dataset record ID
- rendered prompt
- expected response contract
- connector mode
- evaluation policy
- case metadata

Recommended case identifier:

CASE-NNNNNN

Each case produces at least one execution attempt.

---

## 11. Execution Attempts

Retries shall remain explicit.

Each attempt receives:

ATTEMPT-NNN

The initial reference engine uses one attempt per case.

Future retry policies may support:

- no retry
- retry technical failures only
- bounded retry count
- exponential backoff
- provider-directed retry

Retries must never overwrite earlier attempts.

---

## 12. Connector Execution

The engine constructs a canonical connector request and sends it through the
registered connector service.

The engine records:

- request ID
- request hash
- connector ID
- connector version
- subject ID
- model identifier
- canonical messages
- execution parameters
- response status
- response hash
- timing
- usage
- provider metadata
- sanitized errors

Experiments never call models directly.

---

## 13. Observation Preservation

Every connector execution attempt produces an observation artifact.

Observation preservation occurs before scientific evaluation.

The observation must preserve:

- raw rendered prompt
- raw connector response
- request hash
- response hash
- execution status
- timing
- usage
- error state
- cache state
- environment

Evaluation failure must not erase a valid observation.

---

## 14. Evaluation

The execution engine applies a declared evaluator to the preserved response.

PrimeAIExplorer v0.8 initially supports structured-response validity
evaluation.

The evaluator verifies that mock JSON responses contain:

- prediction
- confidence
- abstain

Each evaluation result remains separate from its source observation.

---

## 15. Run-Level Summary

PrimeAIExplorer v0.8 generates deterministic run-level accounting.

The initial summary includes:

- planned case count
- executed case count
- successful connector responses
- failed connector responses
- valid evaluations
- invalid evaluations
- observation count
- evaluation count
- external-access count
- paid-call count
- total measured latency

This summary is descriptive.

It is not yet a substitute for a canonical experiment-level statistical
analysis plan.

---

## 16. Scientific Report

The execution engine generates a report containing:

- scientific scope
- execution protocol
- run accounting
- results
- limitations
- evidence references

The report must state clearly that the deterministic mock connector is not a
frontier model.

---

## 17. Run Manifest

Every completed run shall produce a canonical run manifest.

The run manifest should contain:

- run identity
- lifecycle status
- execution context
- phase records
- case accounting
- artifact inventory
- integrity hashes
- environment
- failure summary
- timestamps

The manifest is the canonical index of the run.

---

## 18. Recommended Run Layout

    results/
    |
    +-- RUN-20260725-000001/
        |
        +-- run_manifest.json
        +-- events.jsonl
        +-- run_statistics.json
        |
        +-- observations/
        |   +-- OBS-0000000001.json
        |
        +-- evaluations/
        |   +-- EVR-0000000001.json
        |
        +-- report/
            +-- scientific_report.md
            +-- report_manifest.json

---

## 19. Event Log

Every execution phase should append a structured event.

Recommended event fields include:

- event sequence
- timestamp
- run ID
- phase
- status
- message
- duration
- artifact
- error

JSON Lines is the canonical initial event format.

---

## 20. Atomic Artifact Creation

Run artifacts shall be written atomically where practical.

Recommended procedure:

1. Render the complete artifact.
2. Write to a temporary path.
3. Flush and close.
4. Validate.
5. Calculate a checksum.
6. Rename atomically.
7. Register only after success.

A partial artifact must not appear as completed evidence.

---

## 21. Deterministic Mode

Identical scientific cases, connector configuration, and canonical inputs
should produce identical scientific response content.

Wall-clock timestamps and measured durations may differ.

Scientific content hashes must remain stable where timestamps are excluded from
the canonical scientific payload.

---

## 22. Failure Handling

The engine distinguishes:

- registry failure
- validation failure
- connector failure
- observation persistence failure
- evaluation failure
- summary failure
- report failure
- finalization failure

A case failure should be preserved without necessarily destroying the entire
run.

A run-level infrastructure failure must be recorded in the manifest when
possible.

---

## 23. Interruption Recovery

Future versions should support recovery after interruption.

Potential recovery mechanisms include:

- phase checkpoints
- idempotent artifact writes
- immutable completed cases
- manifest reconstruction
- registry reconciliation
- unfinished temporary-file cleanup

PrimeAIExplorer v0.8 provides a single-process deterministic reference engine.

---

## 24. Execution Registry

The execution registry records reusable execution profiles.

Initial profiles include:

### EXEC-000001 â€” Deterministic Mock Pipeline

Connector:

CONNECTOR-000001

External access:

false

Cost class:

free

Status:

Active

### EXEC-000002 â€” Replay Pipeline

Status:

Planned

### EXEC-000003 â€” Hosted Model Pipeline

Status:

Disabled

External access:

true

Cost class:

paid

---

## 25. Scientific Safeguards

The execution engine shall not:

- bypass registry governance
- enable paid connectors silently
- hide external access
- hide case failures
- overwrite observations
- overwrite evaluations
- count cache references as new model samples
- fabricate usage
- fabricate model revisions
- claim a mock connector is a language model
- delete partial scientific evidence selectively
- generate conclusions before evidence preservation

---

## 26. Reproducibility Commitment

A run is scientifically useful only when another researcher can determine:

- which configuration was planned
- which registry objects were selected
- which cases executed
- which connector transported each task
- whether external access occurred
- whether financial cost was possible
- which observations were preserved
- which evaluations were applied
- which artifacts were generated
- which failures occurred
- how run integrity was verified

PrimeAIExplorer shall preserve this information.

---

## 27. Guiding Statement

Execution connects scientific objects.

It does not weaken their boundaries.

Plan explicitly.

Validate before execution.

Preserve every attempt.

Evaluate transparently.

Summarize reproducibly.

Report honestly.

Draw conclusions second.

---

End of Document
'@

Set-Content `
    -Path $CanonicalExecutionPath `
    -Value $CanonicalExecution `
    -Encoding UTF8

# ------------------------------------------------------------
# 2. Run Manifest JSON Schema
# ------------------------------------------------------------

$RunManifestSchema = [ordered]@{
    '$schema' = "https://json-schema.org/draft/2020-12/schema"
    '$id' = "https://primenet.local/primeaiexplorer/schemas/run_manifest.schema.json"
    title = "PrimeAIExplorer Canonical Run Manifest"
    description = "Canonical schema for a PrimeAIExplorer execution run."
    type = "object"
    additionalProperties = $false

    required = @(
        "run_id",
        "run_schema_version",
        "status",
        "context",
        "phases",
        "accounting",
        "artifacts",
        "integrity",
        "environment",
        "created_at_utc",
        "completed_at_utc"
    )

    properties = [ordered]@{
        run_id = [ordered]@{
            type = "string"
            pattern = "^RUN-[0-9]{8}-[0-9]{6}$"
        }

        run_schema_version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        status = [ordered]@{
            type = "string"
            enum = @(
                "planned",
                "validating",
                "ready",
                "running",
                "completed",
                "completed_with_failures",
                "failed",
                "cancelled",
                "superseded"
            )
        }

        context = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "experiment_id",
                "dataset_id",
                "prompt_id",
                "connector_id",
                "execution_mode",
                "output_directory"
            )
        }

        phases = [ordered]@{
            type = "array"
            items = [ordered]@{
                type = "object"
                additionalProperties = $true
                required = @(
                    "phase",
                    "status",
                    "started_at_utc",
                    "completed_at_utc",
                    "duration_seconds"
                )
            }
        }

        accounting = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "planned_cases",
                "executed_cases",
                "successful_responses",
                "failed_responses",
                "valid_evaluations",
                "invalid_evaluations",
                "observations",
                "evaluations",
                "external_access_count",
                "paid_call_count"
            )
        }

        artifacts = [ordered]@{
            type = "array"
            items = [ordered]@{
                type = "object"
                additionalProperties = $false
                required = @(
                    "artifact_type",
                    "relative_path",
                    "sha256"
                )
            }
        }

        integrity = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "algorithm",
                "manifest_sha256"
            )
        }

        environment = [ordered]@{
            type = "object"
            additionalProperties = $true
        }

        created_at_utc = [ordered]@{
            type = "string"
            format = "date-time"
        }

        completed_at_utc = [ordered]@{
            type = @("string", "null")
            format = "date-time"
        }
    }
}

$RunManifestSchema |
    ConvertTo-Json -Depth 30 |
    Set-Content `
        -Path $RunManifestSchemaPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 3. Execution Registry
# ------------------------------------------------------------

$RunRegistryRows = @(
    [pscustomobject][ordered]@{
        execution_profile_id = "EXEC-000001"
        title                = "Deterministic Mock Pipeline"
        short_name           = "deterministic_mock_pipeline"
        version              = "0.1.0"
        status               = "Active"
        connector_id         = "CONNECTOR-000001"
        execution_mode       = "local"
        external_access      = "false"
        cost_class           = "free"
        implementation_module = "core.execution_engine"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        execution_profile_id = "EXEC-000002"
        title                = "Replay Pipeline"
        short_name           = "replay_pipeline"
        version              = "0.1.0"
        status               = "Planned"
        connector_id         = "CONNECTOR-000002"
        execution_mode       = "replay"
        external_access      = "false"
        cost_class           = "free"
        implementation_module = ""
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        execution_profile_id = "EXEC-000003"
        title                = "Hosted Model Pipeline"
        short_name           = "hosted_model_pipeline"
        version              = "0.1.0"
        status               = "Disabled"
        connector_id         = "CONNECTOR-000003"
        execution_mode       = "api"
        external_access      = "true"
        cost_class           = "paid"
        implementation_module = ""
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    }
)

$RunRegistryRows |
    Export-Csv `
        -Path $RunRegistryCsvPath `
        -NoTypeInformation `
        -Encoding UTF8

$RunRegistryObject = [ordered]@{
    registry_name = "PrimeAIExplorer Execution Registry"
    registry_version = "0.8.0"
    run_schema_version = "0.8.0"
    updated_date = "2026-07-25"
    execution_profiles = @(
        foreach ($Row in $RunRegistryRows) {
            [ordered]@{
                execution_profile_id = $Row.execution_profile_id
                title = $Row.title
                short_name = $Row.short_name
                version = $Row.version
                status = $Row.status
                connector_id = $Row.connector_id
                execution_mode = $Row.execution_mode
                external_access = ($Row.external_access -eq "true")
                cost_class = $Row.cost_class
                implementation_module = $Row.implementation_module
                created_date = $Row.created_date
                modified_date = $Row.modified_date
            }
        }
    )
}

$RunRegistryObject |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -Path $RunRegistryJsonPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 4. Execution Context
# ------------------------------------------------------------

$ExecutionContextModule = @'
"""Immutable execution context for PrimeAIExplorer runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import platform
from typing import Any


RUN_SCHEMA_VERSION = "0.8.0"
PRIME_AI_EXPLORER_VERSION = "0.8.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_run_id(
    sequence: int,
    *,
    run_date: date | None = None,
) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Run sequence must be an integer.")

    if sequence < 1 or sequence > 999_999:
        raise ValueError(
            "Run sequence must be between 1 and 999,999."
        )

    selected_date = run_date or datetime.now(timezone.utc).date()

    return (
        f"RUN-{selected_date.strftime('%Y%m%d')}-"
        f"{sequence:06d}"
    )


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    run_id: str
    experiment_id: str
    experiment_version: str
    dataset_id: str
    dataset_version: str
    prompt_id: str
    prompt_version: str
    connector_id: str
    connector_version: str
    subject_id: str
    model_identifier: str
    execution_mode: str
    output_directory: str
    random_seed: int
    created_at_utc: str
    run_schema_version: str = RUN_SCHEMA_VERSION
    primeaiexplorer_version: str = PRIME_AI_EXPLORER_VERSION

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        experiment_id: str,
        experiment_version: str,
        dataset_id: str,
        dataset_version: str,
        prompt_id: str,
        prompt_version: str,
        connector_id: str,
        connector_version: str,
        subject_id: str,
        model_identifier: str,
        execution_mode: str,
        results_root: str | Path,
        random_seed: int,
        run_date: date | None = None,
    ) -> "ExecutionContext":
        run_id = canonical_run_id(
            sequence,
            run_date=run_date,
        )
        output_directory = str(
            Path(results_root).resolve() / run_id
        )

        return cls(
            run_id=run_id,
            experiment_id=experiment_id,
            experiment_version=experiment_version,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            connector_id=connector_id,
            connector_version=connector_version,
            subject_id=subject_id,
            model_identifier=model_identifier,
            execution_mode=execution_mode,
            output_directory=output_directory,
            random_seed=random_seed,
            created_at_utc=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["environment"] = {
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        }
        return value


__all__ = [
    "ExecutionContext",
    "PRIME_AI_EXPLORER_VERSION",
    "RUN_SCHEMA_VERSION",
    "canonical_run_id",
    "utc_now_iso",
]
'@

Set-Content `
    -Path $ExecutionContextPath `
    -Value $ExecutionContextModule `
    -Encoding UTF8

# ------------------------------------------------------------
# 5. Registry Loader
# ------------------------------------------------------------

$RegistryLoaderModule = @'
"""Canonical registry loading and relationship validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


class RegistryError(RuntimeError):
    """Raised when a canonical registry is missing or invalid."""


class RegistryLoader:
    """Load canonical CSV registries from one repository root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def _load_csv(
        self,
        relative_path: str,
    ) -> list[dict[str, str]]:
        path = self.root / relative_path

        if not path.exists():
            raise RegistryError(
                f"Registry does not exist: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as stream:
            rows = list(csv.DictReader(stream))

        if not rows:
            raise RegistryError(
                f"Registry contains no records: {path}"
            )

        return rows

    @staticmethod
    def _index(
        rows: Iterable[dict[str, str]],
        key: str,
    ) -> dict[str, dict[str, str]]:
        index: dict[str, dict[str, str]] = {}

        for row in rows:
            identifier = row.get(key, "").strip()

            if not identifier:
                raise RegistryError(
                    f"Registry record is missing key: {key}"
                )

            if identifier in index:
                raise RegistryError(
                    f"Duplicate registry identifier: {identifier}"
                )

            index[identifier] = row

        return index

    def experiments(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "experiments/experiment_registry.csv"
            ),
            "experiment_id",
        )

    def datasets(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "datasets/dataset_registry.csv"
            ),
            "dataset_id",
        )

    def prompts(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "prompts/prompt_registry.csv"
            ),
            "prompt_id",
        )

    def connectors(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "connectors/connector_registry.csv"
            ),
            "connector_id",
        )

    def execution_profiles(
        self,
    ) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "executions/run_registry.csv"
            ),
            "execution_profile_id",
        )

    def validate_selection(
        self,
        *,
        experiment_id: str,
        dataset_id: str,
        prompt_id: str,
        connector_id: str,
        execution_profile_id: str,
        free_mode: bool = True,
    ) -> dict[str, dict[str, str]]:
        experiments = self.experiments()
        datasets = self.datasets()
        prompts = self.prompts()
        connectors = self.connectors()
        profiles = self.execution_profiles()

        try:
            experiment = experiments[experiment_id]
            dataset = datasets[dataset_id]
            prompt = prompts[prompt_id]
            connector = connectors[connector_id]
            profile = profiles[execution_profile_id]
        except KeyError as error:
            raise RegistryError(
                f"Unknown registry identifier: {error.args[0]}"
            ) from error

        if prompt["experiment_id"] != experiment_id:
            raise RegistryError(
                "Prompt does not reference the selected experiment."
            )

        if prompt["dataset_id"] != dataset_id:
            raise RegistryError(
                "Prompt does not reference the selected dataset."
            )

        if profile["connector_id"] != connector_id:
            raise RegistryError(
                "Execution profile does not use the selected connector."
            )

        if connector["status"] != "Active":
            raise RegistryError(
                f"Connector is not active: {connector_id}"
            )

        if profile["status"] != "Active":
            raise RegistryError(
                f"Execution profile is not active: "
                f"{execution_profile_id}"
            )

        if free_mode:
            if connector["external_access"].lower() != "false":
                raise RegistryError(
                    "Free mode prohibits external-access connectors."
                )

            if connector["cost_class"].lower() != "free":
                raise RegistryError(
                    "Free mode prohibits non-free connectors."
                )

            if profile["external_access"].lower() != "false":
                raise RegistryError(
                    "Free mode prohibits external execution profiles."
                )

            if profile["cost_class"].lower() != "free":
                raise RegistryError(
                    "Free mode prohibits paid execution profiles."
                )

        return {
            "experiment": experiment,
            "dataset": dataset,
            "prompt": prompt,
            "connector": connector,
            "execution_profile": profile,
        }


__all__ = [
    "RegistryError",
    "RegistryLoader",
]
'@

Set-Content `
    -Path $RegistryLoaderPath `
    -Value $RegistryLoaderModule `
    -Encoding UTF8

# ------------------------------------------------------------
# 6. Execution Engine
# ------------------------------------------------------------

$ExecutionEngineModule = @'
"""Deterministic end-to-end execution engine for PrimeAIExplorer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Iterable, Sequence

from connectors import (
    ConnectorMessage,
    ConnectorRequest,
    ConnectorStatus,
    DeterministicMockConnector,
    MessageRole,
    MockMode,
    canonical_request_id,
)
from core.evaluation import evaluate_required_json_fields
from core.execution_context import ExecutionContext
from core.observation import (
    DatasetLink,
    ExperimentLink,
    ObservationRecord,
    ObservationStatus,
    PromptLink,
    SubjectLink,
)
from core.registry_loader import RegistryLoader
from core.report import ReportSection, build_experiment_report


EXECUTION_ENGINE_VERSION = "0.8.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def write_text_atomic(
    path: str | Path,
    payload: str,
) -> Path:
    final_path = Path(path)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = final_path.with_name(
        final_path.name + ".tmp"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        temporary_path.replace(final_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return final_path


@dataclass(frozen=True, slots=True)
class ExecutionCase:
    case_id: str
    condition_id: str
    record_id: str
    user_prompt: str
    required_response_fields: tuple[str, ...] = (
        "prediction",
        "confidence",
        "abstain",
    )

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("Case ID cannot be empty.")

        if not self.condition_id:
            raise ValueError("Condition ID cannot be empty.")

        if not self.user_prompt:
            raise ValueError("User prompt cannot be empty.")


class RunEventLog:
    """Append-only JSON Lines execution event log."""

    def __init__(
        self,
        path: str | Path,
        run_id: str,
    ) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self.sequence = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        phase: str,
        status: str,
        message: str,
        duration_seconds: float | None = None,
        artifact: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        self.sequence += 1

        event = {
            "event_sequence": self.sequence,
            "timestamp_utc": utc_now_iso(),
            "run_id": self.run_id,
            "phase": phase,
            "status": status,
            "message": message,
            "duration_seconds": duration_seconds,
            "artifact": artifact,
            "error": error,
        }

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

        return event


class ExecutionEngine:
    """Execute deterministic scientific cases end to end."""

    def __init__(
        self,
        *,
        root: str | Path,
        context: ExecutionContext,
        execution_profile_id: str = "EXEC-000001",
    ) -> None:
        self.root = Path(root).resolve()
        self.context = context
        self.execution_profile_id = execution_profile_id
        self.output_directory = Path(
            context.output_directory
        )
        self.loader = RegistryLoader(self.root)

    def run(
        self,
        cases: Sequence[ExecutionCase],
    ) -> dict[str, Any]:
        if not cases:
            raise ValueError(
                "At least one execution case is required."
            )

        output = self.output_directory
        observations_directory = output / "observations"
        evaluations_directory = output / "evaluations"
        report_directory = output / "report"

        output.mkdir(parents=True, exist_ok=True)
        observations_directory.mkdir(exist_ok=True)
        evaluations_directory.mkdir(exist_ok=True)

        event_log = RunEventLog(
            output / "events.jsonl",
            self.context.run_id,
        )

        created_at = utc_now_iso()
        phases: list[dict[str, Any]] = []
        artifacts: list[dict[str, str]] = []

        accounting = {
            "planned_cases": len(cases),
            "executed_cases": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "valid_evaluations": 0,
            "invalid_evaluations": 0,
            "observations": 0,
            "evaluations": 0,
            "external_access_count": 0,
            "paid_call_count": 0,
            "total_latency_seconds": 0.0,
        }

        def phase(
            name: str,
            operation,
        ):
            started = utc_now_iso()
            clock = time.perf_counter()

            event_log.append(
                phase=name,
                status="started",
                message=f"Phase started: {name}",
            )

            try:
                result = operation()
            except Exception as error:
                duration = time.perf_counter() - clock
                completed = utc_now_iso()

                phases.append(
                    {
                        "phase": name,
                        "status": "failed",
                        "started_at_utc": started,
                        "completed_at_utc": completed,
                        "duration_seconds": duration,
                        "message": str(error),
                    }
                )

                event_log.append(
                    phase=name,
                    status="failed",
                    message=f"Phase failed: {name}",
                    duration_seconds=duration,
                    error=str(error),
                )
                raise

            duration = time.perf_counter() - clock
            completed = utc_now_iso()

            phases.append(
                {
                    "phase": name,
                    "status": "completed",
                    "started_at_utc": started,
                    "completed_at_utc": completed,
                    "duration_seconds": duration,
                    "message": f"Phase completed: {name}",
                }
            )

            event_log.append(
                phase=name,
                status="completed",
                message=f"Phase completed: {name}",
                duration_seconds=duration,
            )

            return result

        selection = phase(
            "validate",
            lambda: self.loader.validate_selection(
                experiment_id=self.context.experiment_id,
                dataset_id=self.context.dataset_id,
                prompt_id=self.context.prompt_id,
                connector_id=self.context.connector_id,
                execution_profile_id=self.execution_profile_id,
                free_mode=True,
            ),
        )

        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION
        )

        observation_ids: list[str] = []
        evaluation_ids: list[str] = []

        def execute_cases() -> None:
            for index, case in enumerate(cases, start=1):
                request = ConnectorRequest(
                    request_id=canonical_request_id(index),
                    connector_id=connector.connector_id,
                    connector_version=connector.connector_version,
                    subject_id=self.context.subject_id,
                    model_identifier=self.context.model_identifier,
                    messages=(
                        ConnectorMessage(
                            role=MessageRole.SYSTEM,
                            content=(
                                "Return a deterministic JSON object "
                                "with prediction, confidence, and abstain."
                            ),
                        ),
                        ConnectorMessage(
                            role=MessageRole.USER,
                            content=case.user_prompt,
                        ),
                    ),
                    parameters={
                        "seed": self.context.random_seed,
                        "case_id": case.case_id,
                    },
                    response_format={
                        "type": "json_object",
                    },
                    timeout_seconds=30.0,
                    metadata={
                        "run_id": self.context.run_id,
                        "case_id": case.case_id,
                        "condition_id": case.condition_id,
                    },
                )

                response = connector.execute(request)
                accounting["executed_cases"] += 1
                accounting["total_latency_seconds"] += (
                    response.timing.latency_seconds
                )

                if response.provider_metadata.get(
                    "external_access"
                ):
                    accounting["external_access_count"] += 1

                if response.provider_metadata.get(
                    "cost_incurred"
                ):
                    accounting["paid_call_count"] += 1

                if response.status is ConnectorStatus.SUCCEEDED:
                    accounting["successful_responses"] += 1
                    observation_status = ObservationStatus.SUCCEEDED
                else:
                    accounting["failed_responses"] += 1
                    observation_status = ObservationStatus.FAILED

                observation_id = f"OBS-{index:010d}"
                observation_ids.append(observation_id)

                observation = ObservationRecord(
                    observation_id=observation_id,
                    run_id=self.context.run_id,
                    condition_id=case.condition_id,
                    attempt_id="ATTEMPT-001",
                    status=observation_status,
                    experiment=ExperimentLink(
                        experiment_id=self.context.experiment_id,
                        experiment_version=(
                            self.context.experiment_version
                        ),
                        experimental_universe="PrimeNet",
                        hypothesis_id=None,
                    ),
                    dataset=DatasetLink(
                        dataset_id=self.context.dataset_id,
                        dataset_version=self.context.dataset_version,
                        partition="calibration",
                        record_id=case.record_id,
                        artifact_sha256=None,
                    ),
                    prompt=PromptLink(
                        prompt_id=self.context.prompt_id,
                        prompt_version=self.context.prompt_version,
                        rendered_prompt_sha256=sha256_text(
                            case.user_prompt
                        ),
                        response_schema_id="RESPONSE-000001",
                        response_schema_version="0.1.0",
                    ),
                    subject=SubjectLink(
                        subject_id=self.context.subject_id,
                        subject_type="deterministic_baseline",
                        provider="PrimeAIExplorer",
                        connector=connector.connector_id,
                        connector_version=(
                            connector.connector_version
                        ),
                        model_identifier=(
                            self.context.model_identifier
                        ),
                        reported_model_version="0.1.0",
                    ),
                    execution={
                        "mode": "local",
                        "parameters": dict(request.parameters),
                        "connector_status": response.status.value,
                    },
                    timing={
                        "created_at_utc": (
                            response.timing.started_at_utc
                        ),
                        "started_at_utc": (
                            response.timing.started_at_utc
                        ),
                        "completed_at_utc": (
                            response.timing.completed_at_utc
                        ),
                        "latency_seconds": (
                            response.timing.latency_seconds
                        ),
                    },
                    request={
                        "request_sha256": response.request_sha256,
                        "rendered_prompt": case.user_prompt,
                    },
                    response={
                        "raw_text": response.raw_text,
                        "response_sha256": (
                            response.response_sha256
                        ),
                        "finish_reason": response.finish_reason,
                        "provider_metadata": dict(
                            response.provider_metadata
                        ),
                        "usage": response.usage.to_dict(),
                    },
                    integrity={
                        "algorithm": "SHA-256",
                        "configuration_sha256": sha256_text(
                            canonical_json(
                                {
                                    "context": (
                                        self.context.to_dict()
                                    ),
                                    "case_id": case.case_id,
                                    "request_sha256": (
                                        response.request_sha256
                                    ),
                                }
                            )
                        ),
                    },
                    cache={
                        "was_cached": False,
                        "cache_key": None,
                        "source_observation_id": None,
                    },
                    error={
                        "category": response.error.category,
                        "message": response.error.message,
                        "retryable": response.error.retryable,
                    },
                    environment={
                        "primeaiexplorer_version": "0.8.0",
                        "python_version": (
                            platform.python_version()
                        ),
                        "operating_system": platform.system(),
                    },
                    evaluation={
                        "state": "pending",
                    },
                )

                observation_path = (
                    observations_directory
                    / f"{observation_id}.json"
                )
                observation.write_atomic(observation_path)
                accounting["observations"] += 1

                event_log.append(
                    phase="preserve_observations",
                    status="completed",
                    message=(
                        f"Observation preserved: "
                        f"{observation_id}"
                    ),
                    artifact=str(
                        observation_path.relative_to(output)
                    ),
                )

                evaluation_sequence = index
                evaluation = evaluate_required_json_fields(
                    sequence=evaluation_sequence,
                    observation_id=observation_id,
                    observation_schema_version="0.3.0",
                    response_sha256=response.response_sha256,
                    raw_text=response.raw_text or "",
                    required_fields=(
                        case.required_response_fields
                    ),
                )

                evaluation_id = (
                    evaluation.evaluation_result_id
                )
                evaluation_ids.append(evaluation_id)

                evaluation_path = (
                    evaluations_directory
                    / f"{evaluation_id}.json"
                )
                evaluation.write_atomic(evaluation_path)
                accounting["evaluations"] += 1

                if evaluation.validity["is_valid"]:
                    accounting["valid_evaluations"] += 1
                else:
                    accounting["invalid_evaluations"] += 1

                event_log.append(
                    phase="evaluate",
                    status="completed",
                    message=(
                        f"Evaluation preserved: "
                        f"{evaluation_id}"
                    ),
                    artifact=str(
                        evaluation_path.relative_to(output)
                    ),
                )

        phase("execute", execute_cases)

        run_statistics = {
            "run_id": self.context.run_id,
            "summary_type": "descriptive_run_accounting",
            "generated_at_utc": utc_now_iso(),
            "accounting": dict(accounting),
            "scientific_note": (
                "This run used a deterministic mock connector. "
                "It is pipeline-validation evidence, not "
                "frontier-model evidence."
            ),
        }

        run_statistics_path = output / "run_statistics.json"

        phase(
            "summarize",
            lambda: write_text_atomic(
                run_statistics_path,
                json.dumps(
                    run_statistics,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
            ),
        )

        report = phase(
            "report",
            lambda: build_experiment_report(
                sequence=1,
                title=(
                    "PrimeAIExplorer v0.8 Deterministic "
                    "Execution Report"
                ),
                authors=["Jinhua Liao"],
                experiment_id=self.context.experiment_id,
                experiment_version=(
                    self.context.experiment_version
                ),
                sections=[
                    ReportSection(
                        section_id="scope",
                        title="Scientific Scope",
                        content=(
                            "This run validates the complete local "
                            "PrimeAIExplorer execution pipeline."
                        ),
                    ),
                    ReportSection(
                        section_id="protocol",
                        title="Execution Protocol",
                        content=(
                            "All cases were executed through "
                            "CONNECTOR-000001, the deterministic "
                            "mock connector. No external access or "
                            "paid model call occurred."
                        ),
                    ),
                    ReportSection(
                        section_id="results",
                        title="Results",
                        content=(
                            f"Planned cases: "
                            f"{accounting['planned_cases']}\n\n"
                            f"Executed cases: "
                            f"{accounting['executed_cases']}\n\n"
                            f"Valid evaluations: "
                            f"{accounting['valid_evaluations']}\n\n"
                            f"Invalid evaluations: "
                            f"{accounting['invalid_evaluations']}"
                        ),
                    ),
                    ReportSection(
                        section_id="limitations",
                        title="Limitations",
                        content=(
                            "The deterministic mock connector is "
                            "not a language model. These results "
                            "validate infrastructure only and must "
                            "not be interpreted as evidence about "
                            "foundation-model intelligence."
                        ),
                    ),
                ],
                observation_ids=observation_ids,
                evaluation_result_ids=evaluation_ids,
                statistical_summary_ids=[],
            ),
        )

        report_paths = report.write_atomic(report_directory)

        artifact_paths = [
            output / "events.jsonl",
            run_statistics_path,
            *sorted(observations_directory.glob("*.json")),
            *sorted(evaluations_directory.glob("*.json")),
            report_paths["markdown"],
            report_paths["manifest"],
        ]

        for artifact_path in artifact_paths:
            relative = artifact_path.relative_to(output)

            if relative.name == "events.jsonl":
                artifact_type = "event_log"
            elif relative.name == "run_statistics.json":
                artifact_type = "run_statistics"
            elif "observations" in relative.parts:
                artifact_type = "observation"
            elif "evaluations" in relative.parts:
                artifact_type = "evaluation"
            elif relative.name.endswith(".md"):
                artifact_type = "scientific_report"
            else:
                artifact_type = "report_manifest"

            artifacts.append(
                {
                    "artifact_type": artifact_type,
                    "relative_path": relative.as_posix(),
                    "sha256": sha256(
                        artifact_path.read_bytes()
                    ).hexdigest(),
                }
            )

        final_status = (
            "completed"
            if (
                accounting["failed_responses"] == 0
                and accounting["invalid_evaluations"] == 0
            )
            else "completed_with_failures"
        )

        completed_at = utc_now_iso()

        manifest_without_hash = {
            "run_id": self.context.run_id,
            "run_schema_version": "0.8.0",
            "status": final_status,
            "context": self.context.to_dict(),
            "selection": selection,
            "phases": phases,
            "accounting": accounting,
            "artifacts": artifacts,
            "environment": {
                "primeaiexplorer_version": "0.8.0",
                "execution_engine_version": (
                    EXECUTION_ENGINE_VERSION
                ),
                "python_version": platform.python_version(),
                "operating_system": platform.system(),
                "platform": platform.platform(),
            },
            "created_at_utc": created_at,
            "completed_at_utc": completed_at,
        }

        manifest_hash = sha256_text(
            canonical_json(manifest_without_hash)
        )

        manifest = {
            **manifest_without_hash,
            "integrity": {
                "algorithm": "SHA-256",
                "manifest_sha256": manifest_hash,
            },
        }

        manifest_path = output / "run_manifest.json"

        write_text_atomic(
            manifest_path,
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )

        event_log.append(
            phase="finalize",
            status="completed",
            message=(
                f"Run finalized with status: {final_status}"
            ),
            artifact="run_manifest.json",
        )

        return manifest


__all__ = [
    "ExecutionCase",
    "ExecutionEngine",
    "RunEventLog",
    "canonical_json",
    "sha256_text",
    "utc_now_iso",
    "write_text_atomic",
]
'@

Set-Content `
    -Path $ExecutionEnginePath `
    -Value $ExecutionEngineModule `
    -Encoding UTF8

# ------------------------------------------------------------
# 7. Unit Tests
# ------------------------------------------------------------

$ExecutionTests = @'
"""Tests for PrimeAIExplorer v0.8 execution engine."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from core.execution_context import (
    ExecutionContext,
    canonical_run_id,
)
from core.execution_engine import (
    ExecutionCase,
    ExecutionEngine,
)
from core.registry_loader import (
    RegistryError,
    RegistryLoader,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RunIdentifierTests(unittest.TestCase):
    def test_canonical_run_identifier(self) -> None:
        self.assertEqual(
            canonical_run_id(
                1,
                run_date=date(2026, 7, 25),
            ),
            "RUN-20260725-000001",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_run_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_run_id(True)


class ExecutionContextTests(unittest.TestCase):
    def test_context_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = ExecutionContext.create(
                sequence=1,
                run_date=date(2026, 7, 25),
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                dataset_id="DS-000001",
                dataset_version="0.1.0",
                prompt_id="PROMPT-000001",
                prompt_version="0.1.0",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                execution_mode="local",
                results_root=directory,
                random_seed=20260725,
            )

            self.assertEqual(
                context.run_id,
                "RUN-20260725-000001",
            )
            self.assertTrue(
                context.output_directory.endswith(
                    "RUN-20260725-000001"
                )
            )
            self.assertEqual(
                context.primeaiexplorer_version,
                "0.8.0",
            )


class RegistryLoaderTests(unittest.TestCase):
    def test_valid_free_selection(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        selection = loader.validate_selection(
            experiment_id="EXP-000001",
            dataset_id="DS-000001",
            prompt_id="PROMPT-000001",
            connector_id="CONNECTOR-000001",
            execution_profile_id="EXEC-000001",
            free_mode=True,
        )

        self.assertEqual(
            selection["connector"]["cost_class"],
            "free",
        )
        self.assertEqual(
            selection["connector"]["external_access"],
            "false",
        )

    def test_disabled_paid_connector_rejected(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        with self.assertRaises(RegistryError):
            loader.validate_selection(
                experiment_id="EXP-000001",
                dataset_id="DS-000001",
                prompt_id="PROMPT-000001",
                connector_id="CONNECTOR-000003",
                execution_profile_id="EXEC-000003",
                free_mode=True,
            )

    def test_unknown_identifier_rejected(self) -> None:
        loader = RegistryLoader(PROJECT_ROOT)

        with self.assertRaises(RegistryError):
            loader.validate_selection(
                experiment_id="EXP-999999",
                dataset_id="DS-000001",
                prompt_id="PROMPT-000001",
                connector_id="CONNECTOR-000001",
                execution_profile_id="EXEC-000001",
            )


class ExecutionCaseTests(unittest.TestCase):
    def test_empty_prompt_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionCase(
                case_id="CASE-000001",
                condition_id="COND-EXP000001-001",
                record_id="REC-DS000001-0000000001",
                user_prompt="",
            )


class ExecutionEngineTests(unittest.TestCase):
    def build_context(
        self,
        results_root: str,
    ) -> ExecutionContext:
        return ExecutionContext.create(
            sequence=1,
            run_date=date(2026, 7, 25),
            experiment_id="EXP-000001",
            experiment_version="0.1.0",
            dataset_id="DS-000001",
            dataset_version="0.1.0",
            prompt_id="PROMPT-000001",
            prompt_version="0.1.0",
            connector_id="CONNECTOR-000001",
            connector_version="0.1.0",
            subject_id="SUBJECT-000001",
            model_identifier="deterministic-mock",
            execution_mode="local",
            results_root=results_root,
            random_seed=20260725,
        )

    def build_cases(self) -> list[ExecutionCase]:
        return [
            ExecutionCase(
                case_id="CASE-000001",
                condition_id="COND-EXP000001-001",
                record_id="REC-DS000001-0000000001",
                user_prompt=(
                    "Prime gaps: 2, 4, 2, 4, 6, 2. "
                    "Return a structured prediction."
                ),
            ),
            ExecutionCase(
                case_id="CASE-000002",
                condition_id="COND-EXP000001-002",
                record_id="REC-DS000001-0000000002",
                user_prompt=(
                    "Prime gaps: 6, 4, 2, 4, 6, 6. "
                    "Return a structured prediction."
                ),
            ),
        ]

    def test_empty_case_list_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=self.build_context(directory),
            )

            with self.assertRaises(ValueError):
                engine.run([])

    def test_end_to_end_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            manifest = engine.run(self.build_cases())

            self.assertEqual(
                manifest["status"],
                "completed",
            )
            self.assertEqual(
                manifest["accounting"]["planned_cases"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["executed_cases"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["observations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["evaluations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"][
                    "external_access_count"
                ],
                0,
            )
            self.assertEqual(
                manifest["accounting"]["paid_call_count"],
                0,
            )

            output = Path(context.output_directory)

            self.assertTrue(
                (output / "run_manifest.json").exists()
            )
            self.assertTrue(
                (output / "events.jsonl").exists()
            )
            self.assertTrue(
                (output / "run_statistics.json").exists()
            )
            self.assertTrue(
                (
                    output
                    / "report"
                    / "scientific_report.md"
                ).exists()
            )

            observation_files = list(
                (output / "observations").glob("*.json")
            )
            evaluation_files = list(
                (output / "evaluations").glob("*.json")
            )

            self.assertEqual(len(observation_files), 2)
            self.assertEqual(len(evaluation_files), 2)

    def test_mock_run_has_no_external_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            engine.run(self.build_cases())

            manifest = json.loads(
                (
                    Path(context.output_directory)
                    / "run_manifest.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(
                manifest["accounting"][
                    "external_access_count"
                ],
                0,
            )
            self.assertEqual(
                manifest["accounting"]["paid_call_count"],
                0,
            )

    def test_structured_responses_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.build_context(directory)
            engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=context,
            )

            manifest = engine.run(self.build_cases())

            self.assertEqual(
                manifest["accounting"]["valid_evaluations"],
                2,
            )
            self.assertEqual(
                manifest["accounting"]["invalid_evaluations"],
                0,
            )

    def test_scientific_response_content_is_deterministic(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            first_context = self.build_context(
                first_directory
            )
            first_engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=first_context,
            )
            first_engine.run(self.build_cases())

            first_observation = json.loads(
                (
                    Path(first_context.output_directory)
                    / "observations"
                    / "OBS-0000000001.json"
                ).read_text(encoding="utf-8")
            )

        with tempfile.TemporaryDirectory() as second_directory:
            second_context = self.build_context(
                second_directory
            )
            second_engine = ExecutionEngine(
                root=PROJECT_ROOT,
                context=second_context,
            )
            second_engine.run(self.build_cases())

            second_observation = json.loads(
                (
                    Path(second_context.output_directory)
                    / "observations"
                    / "OBS-0000000001.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(
            first_observation["response"]["raw_text"],
            second_observation["response"]["raw_text"],
        )
        self.assertEqual(
            first_observation["response"][
                "response_sha256"
            ],
            second_observation["response"][
                "response_sha256"
            ],
        )


if __name__ == "__main__":
    unittest.main()
'@

Set-Content `
    -Path $ExecutionTestPath `
    -Value $ExecutionTests `
    -Encoding UTF8

# ------------------------------------------------------------
# 8. Demonstration Program
# ------------------------------------------------------------

$DemoModule = @'
"""Run the free PrimeAIExplorer v0.8 deterministic demonstration."""

from __future__ import annotations

from pathlib import Path

from core.execution_context import ExecutionContext
from core.execution_engine import (
    ExecutionCase,
    ExecutionEngine,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    context = ExecutionContext.create(
        sequence=1,
        experiment_id="EXP-000001",
        experiment_version="0.1.0",
        dataset_id="DS-000001",
        dataset_version="0.1.0",
        prompt_id="PROMPT-000001",
        prompt_version="0.1.0",
        connector_id="CONNECTOR-000001",
        connector_version="0.1.0",
        subject_id="SUBJECT-000001",
        model_identifier="deterministic-mock",
        execution_mode="local",
        results_root=ROOT / "results",
        random_seed=20260725,
    )

    cases = [
        ExecutionCase(
            case_id="CASE-000001",
            condition_id="COND-EXP000001-001",
            record_id="REC-DS000001-0000000001",
            user_prompt=(
                "Prime gaps: 2, 4, 2, 4, 6, 2. "
                "Return a structured prediction."
            ),
        ),
        ExecutionCase(
            case_id="CASE-000002",
            condition_id="COND-EXP000001-002",
            record_id="REC-DS000001-0000000002",
            user_prompt=(
                "Prime gaps: 6, 4, 2, 4, 6, 6. "
                "Return a structured prediction."
            ),
        ),
        ExecutionCase(
            case_id="CASE-000003",
            condition_id="COND-EXP000001-003",
            record_id="REC-DS000001-0000000003",
            user_prompt=(
                "Prime gaps: 4, 2, 4, 2, 10, 2. "
                "Return a structured prediction."
            ),
        ),
    ]

    engine = ExecutionEngine(
        root=ROOT,
        context=context,
    )

    manifest = engine.run(cases)

    print("=" * 72)
    print("PrimeAIExplorer v0.8 - Deterministic Execution Demo")
    print("=" * 72)
    print()
    print(f"Run ID:             {manifest['run_id']}")
    print(f"Status:             {manifest['status']}")
    print(
        "Planned cases:       "
        f"{manifest['accounting']['planned_cases']}"
    )
    print(
        "Executed cases:      "
        f"{manifest['accounting']['executed_cases']}"
    )
    print(
        "Valid evaluations:   "
        f"{manifest['accounting']['valid_evaluations']}"
    )
    print(
        "External access:     "
        f"{manifest['accounting']['external_access_count']}"
    )
    print(
        "Paid calls:          "
        f"{manifest['accounting']['paid_call_count']}"
    )
    print()
    print(f"Output: {context.output_directory}")
    print()
    print("DEMO PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

Set-Content `
    -Path $DemoPath `
    -Value $DemoModule `
    -Encoding UTF8

# ------------------------------------------------------------
# 9. Version and Changelog
# ------------------------------------------------------------

Set-Content `
    -Path $VersionPath `
    -Value "0.8.0" `
    -Encoding UTF8

$NewChangelogSection = @'
## 0.8.0 - 2026-07-25

### Added

- Canonical Execution Specification.
- Canonical run-manifest JSON Schema.
- Execution-profile registry in CSV and JSON.
- Immutable execution context.
- Canonical run identifiers.
- Canonical registry loader.
- Registry relationship validation.
- Free-mode connector governance.
- Deterministic execution cases.
- End-to-end local execution engine.
- Append-only JSON Lines event log.
- Connector-to-observation integration.
- Observation-to-evaluation integration.
- Deterministic run accounting.
- Scientific report generation.
- Atomic run-manifest writing.
- Free end-to-end demonstration.
- Execution-engine unit tests.

### Scientific policy

A run preserves both what was planned and what occurred.

Disabled, paid, or external-access connectors cannot execute in free mode.

Every connector attempt becomes a preserved observation before evaluation.

Deterministic mock output is infrastructure-validation evidence and must not be
represented as foundation-model evidence.

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

if ($ExistingBody -notmatch "(?m)^## 0\.8\.0 - 2026-07-25") {
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
# 10. Validation
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.8"
Write-Host " Deterministic Execution Engine"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

$RequiredFiles = @(
    $CanonicalExecutionPath,
    $RunManifestSchemaPath,
    $RunRegistryCsvPath,
    $RunRegistryJsonPath,
    $ExecutionContextPath,
    $RegistryLoaderPath,
    $ExecutionEnginePath,
    $ExecutionTestPath,
    $DemoPath,
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
    "PrimeAIExplorer Canonical Execution Specification",
    "RUN-YYYYMMDD-NNNNNN",
    "A scientific run must preserve both what was planned and what actually",
    "Free-Mode Governance",
    "Experiments never call models directly.",
    "Every connector execution attempt produces an observation artifact.",
    "Execution connects scientific objects.",
    "Draw conclusions second."
)

$DocumentContent = Get-Content $CanonicalExecutionPath -Raw

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
    $Schema = Get-Content $RunManifestSchemaPath -Raw |
        ConvertFrom-Json

    if (
        $Schema.title -eq
        "PrimeAIExplorer Canonical Run Manifest"
    ) {
        Write-Host "[PASS] Run manifest schema JSON is valid"
    }
    else {
        Write-Host "[FAIL] Unexpected run manifest schema title"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Run manifest schema JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

$RegistryRows = @(
    Import-Csv $RunRegistryCsvPath
)

if ($RegistryRows.Count -eq 3) {
    Write-Host "[PASS] Execution registry contains 3 profiles"
}
else {
    Write-Host "[FAIL] Unexpected execution-profile count"
    $Failed = $true
}

$DuplicateProfiles = @(
    $RegistryRows |
        Group-Object execution_profile_id |
        Where-Object Count -gt 1
)

if ($DuplicateProfiles.Count -eq 0) {
    Write-Host "[PASS] No duplicate execution profiles"
}
else {
    Write-Host "[FAIL] Duplicate execution profiles detected"
    $Failed = $true
}

$FreeProfile = @(
    $RegistryRows |
        Where-Object execution_profile_id -eq "EXEC-000001"
)[0]

if (
    $FreeProfile.status -eq "Active" -and
    $FreeProfile.external_access -eq "false" -and
    $FreeProfile.cost_class -eq "free"
) {
    Write-Host "[PASS] Deterministic profile is active and free"
}
else {
    Write-Host "[FAIL] Deterministic profile governance is invalid"
    $Failed = $true
}

$PaidProfile = @(
    $RegistryRows |
        Where-Object execution_profile_id -eq "EXEC-000003"
)[0]

if (
    $PaidProfile.status -eq "Disabled" -and
    $PaidProfile.external_access -eq "true" -and
    $PaidProfile.cost_class -eq "paid"
) {
    Write-Host "[PASS] Hosted paid profile remains disabled"
}
else {
    Write-Host "[FAIL] Hosted profile governance is invalid"
    $Failed = $true
}

$Version = (Get-Content $VersionPath -Raw).Trim()

if ($Version -eq "0.8.0") {
    Write-Host "[PASS] VERSION is 0.8.0"
}
else {
    Write-Host "[FAIL] VERSION is not 0.8.0"
    $Failed = $true
}

Write-Host ""
Write-Host "Python compilation:"

Push-Location $Root

try {
    py -m compileall `
        .\connectors `
        .\core `
        .\tests `
        .\examples

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Python compilation failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Python compilation completed"
    }

    Write-Host ""
    Write-Host "Execution-engine tests:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_execution_engine.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Execution-engine tests failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Execution-engine tests passed"
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

    Write-Host ""
    Write-Host "Free deterministic demonstration:"

    py -m examples.run_v08_demo

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] v0.8 demonstration failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] v0.8 demonstration passed"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Canonical execution document line count:"

$LineCount = (Get-Content $CanonicalExecutionPath).Count
Write-Host $LineCount

if ($LineCount -lt 250) {
    Write-Host "[WARN] Canonical execution document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "PRIMEAIEXPLORER v0.8 FAILED"
    exit 1
}

Write-Host ""
Write-Host "PRIMEAIEXPLORER v0.8 PASSED"
