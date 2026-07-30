# ============================================================
# PrimeAIExplorer v0.3
# Step 5 - Observation Foundation
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"

$ArchitectureDir = Join-Path $Root "architecture"
$SchemasDir      = Join-Path $Root "schemas"
$ObservationsDir = Join-Path $Root "observations"
$CoreDir         = Join-Path $Root "core"
$TestsDir        = Join-Path $Root "tests"

$CanonicalObservationPath = Join-Path $ArchitectureDir "Canonical_Observation.md"
$ObservationSchemaPath    = Join-Path $SchemasDir "observation.schema.json"
$RegistryCsvPath          = Join-Path $ObservationsDir "observation_registry.csv"
$RegistryJsonPath         = Join-Path $ObservationsDir "observation_registry.json"
$ObservationModulePath    = Join-Path $CoreDir "observation.py"
$CoreInitPath             = Join-Path $CoreDir "__init__.py"
$ObservationTestPath      = Join-Path $TestsDir "test_observation.py"
$VersionPath              = Join-Path $Root "VERSION"
$ChangelogPath            = Join-Path $Root "CHANGELOG.md"

$RequiredDirectories = @(
    $ArchitectureDir,
    $SchemasDir,
    $ObservationsDir,
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
# 1. Canonical Observation Specification
# ------------------------------------------------------------

$CanonicalObservation = @'
# PrimeAIExplorer Canonical Observation Specification

Version: 0.3.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of a scientific observation
within PrimeAIExplorer.

An observation is the permanent record of one experimental interaction with an
AI subject or deterministic baseline.

The observation is the fundamental unit of scientific evidence produced by
PrimeAIExplorer.

Experiments define questions.

Datasets provide controlled evidence.

Prompts act as scientific instruments.

Observations preserve what happened.

---

## 2. Foundational Principle

Every completed execution attempt shall create an observation record.

Successful responses are observations.

Failed responses are observations.

Timeouts are observations.

Refusals are observations.

Invalid structured outputs are observations.

Cache reuse is recorded as an observation event linked to the original
observation.

Scientific evidence must not disappear merely because an execution was
unsuccessful.

---

## 3. Canonical Observation Identifier

Every observation receives a permanent identifier using this format:

OBS-NNNNNNNNNN

Examples:

- OBS-0000000001
- OBS-0000000002
- OBS-0000123456

Rules:

- Observation identifiers are permanent.
- Observation identifiers shall never be reused.
- Observation records shall not be silently overwritten.
- Corrections create amendments or derived records.
- Original raw evidence remains preserved.
- Sequence allocation must be atomic when concurrent execution is introduced.

---

## 4. Related Identifiers

An observation may reference:

- EXP-NNNNNN for an experiment
- DS-NNNNNN for a dataset
- PROMPT-NNNNNN for a prompt
- RESPONSE-NNNNNN for a response schema
- RUN-YYYYMMDD-NNNNNN for an experiment run
- COND-EXPNNNNNN-NNN for an experimental condition
- SUBJECT-NNNNNN for an AI subject
- ATTEMPT-NNN for an execution attempt
- EVAL-NNNNNN for an evaluator
- CACHE-NNNNNN for a cached artifact

Every identifier must be documented and versioned where applicable.

---

## 5. Observation Lifecycle

Permitted observation statuses include:

- pending
- executing
- succeeded
- failed
- timed_out
- refused
- invalid_response
- cancelled
- cached
- superseded

### pending

The observation record has been allocated but execution has not started.

### executing

The subject interaction is currently running.

### succeeded

A response was captured successfully.

### failed

Execution ended with a technical or provider error.

### timed_out

Execution exceeded the configured timeout.

### refused

The model declined to perform the task.

### invalid_response

A response was captured but did not satisfy the expected contract.

### cancelled

Execution was intentionally stopped.

### cached

The requested scientific configuration reused an existing immutable response.

### superseded

The observation remains preserved but a documented correction or amendment
exists.

---

## 6. Canonical Observation Structure

Every observation record shall contain these logical sections:

- identity
- experiment linkage
- dataset linkage
- prompt linkage
- subject linkage
- execution configuration
- timing
- usage
- request evidence
- response evidence
- integrity
- cache provenance
- error evidence
- environment
- evaluation state
- governance

---

## 7. Identity

Required identity fields include:

- observation_id
- observation_schema_version
- run_id
- condition_id
- attempt_id
- status
- created_at_utc
- started_at_utc
- completed_at_utc

Timestamps shall use UTC and ISO 8601 formatting.

Example:

    observation_id: OBS-0000000001
    observation_schema_version: 0.3.0
    run_id: RUN-20260725-000001
    condition_id: COND-EXP000001-001
    attempt_id: ATTEMPT-001
    status: succeeded

---

## 8. Experiment Linkage

Every observation must reference:

- experiment ID
- experiment version
- hypothesis ID when applicable
- experimental universe
- execution protocol version

The observation must remain interpretable even after newer experiment versions
are introduced.

---

## 9. Dataset Linkage

Every observation should reference:

- dataset ID
- dataset version
- partition
- record ID
- dataset artifact checksum
- source coordinate or source window
- target record identifier

The exact visible dataset content must be reconstructable.

---

## 10. Prompt Linkage

Every observation must reference:

- prompt ID
- prompt version
- rendered prompt hash
- canonicalization version
- provider adaptation version
- provider-rendered prompt hash when applicable
- response schema ID
- response schema version

Raw rendered prompt content should be preserved directly or reproducible from
immutable prompt artifacts and recorded rendering variables.

---

## 11. Subject Linkage

Every observation must describe the experimental subject.

Recommended fields include:

- subject ID
- subject type
- provider
- connector
- connector version
- model identifier
- reported model version
- model revision when available
- access method
- context limit
- tool availability

Absence of an exact provider-side model revision must be recorded explicitly.

---

## 12. Execution Configuration

The execution configuration should record:

- temperature
- top-p
- top-k
- random seed when supported
- maximum output tokens
- stop sequences
- response format
- timeout
- retry policy
- tool configuration
- safety configuration when exposed
- provider-specific parameters

Unknown or unsupported parameters should not be represented as though they were
controlled.

---

## 13. Timing

Timing fields may include:

- queued timestamp
- started timestamp
- first-token timestamp
- completed timestamp
- queue duration
- connection duration
- time to first token
- generation duration
- total latency

All timing units must be explicit.

Monotonic clocks should be used for duration measurement where practical.

UTC wall-clock timestamps should be preserved for provenance.

---

## 14. Usage

Usage fields may include:

- input tokens
- output tokens
- total tokens
- cached input tokens
- reasoning tokens when reported
- characters
- bytes
- message count
- observation count
- estimated cost
- billing currency
- usage source

Usage values reported by a provider must be distinguished from local estimates.

PrimeAIExplorer v0.3 performs no paid model calls.

---

## 15. Request Evidence

Request evidence should preserve:

- canonical request representation
- rendered prompt
- ordered message roles
- prompt variables
- provider request payload with secrets removed
- request hash
- request byte count
- request token estimate

Secrets, credentials, authorization headers, and API keys shall never be stored
in observation artifacts.

---

## 16. Response Evidence

Response evidence should preserve:

- raw provider response
- raw model text
- structured response when available
- finish reason
- refusal details
- tool calls
- citations when returned
- provider metadata
- response hash
- response byte count

The raw response shall not be silently normalized or rewritten.

Parsing produces a derived artifact linked to the raw response.

---

## 17. Raw and Derived Evidence

PrimeAIExplorer distinguishes raw evidence from derived evidence.

Raw evidence includes:

- rendered request
- provider response
- model text
- provider error
- timing measurements
- provider usage report

Derived evidence includes:

- parsed fields
- normalized numbers
- extracted predictions
- validity flags
- evaluation scores
- statistical summaries

Derived artifacts must reference their source observation.

Raw evidence remains immutable.

---

## 18. Integrity

Every observation should include cryptographic hashes for applicable artifacts.

SHA-256 is the default algorithm.

Potential hashes include:

- request hash
- prompt hash
- response hash
- raw artifact hash
- normalized artifact hash
- configuration hash
- environment hash

Hashes must identify their canonicalization procedure.

A changed hash indicates a changed artifact.

---

## 19. Cache Provenance

Cached observations must be transparent.

A cached observation should record:

- cached status
- cache key
- source observation ID
- source run ID
- original execution timestamp
- cache lookup timestamp
- cache policy version
- equivalence justification

Cache reuse must not create the appearance of a new independent model sample.

Statistical analysis must distinguish original executions from cache reuse.

---

## 20. Failure Evidence

Failed executions are scientifically relevant.

A failure record should preserve:

- failure category
- error type
- error code
- sanitized error message
- provider request identifier when safe
- retry eligibility
- retry number
- final-attempt flag
- partial response when available
- timing
- configuration

Retries create additional attempt records rather than replacing earlier
failures.

---

## 21. Error Categories

Recommended error categories include:

- configuration_error
- validation_error
- connector_error
- authentication_error
- authorization_error
- rate_limit
- timeout
- network_error
- provider_error
- context_limit
- invalid_response
- parser_error
- cancelled
- unknown

Credentials and sensitive provider details must be removed from stored error
messages.

---

## 22. Environment Capture

Every observation or run manifest should capture:

- PrimeAIExplorer version
- source-control commit
- Python version
- operating system
- architecture
- dependency versions
- connector version
- evaluator version
- statistics version
- hostname policy
- timezone
- locale

Personally identifying machine information should be minimized.

Environment capture should support reproducibility without exposing unnecessary
private information.

---

## 23. Evaluation State

Observation capture and observation evaluation are separate stages.

Recommended evaluation states include:

- not_started
- pending
- valid
- invalid
- scored
- review_required
- reviewed
- excluded_with_reason

Evaluation shall not overwrite raw observation fields.

Evaluation artifacts must identify:

- evaluator ID
- evaluator version
- evaluation timestamp
- metric values
- validity result
- exclusion reason
- review status

---

## 24. Observation Immutability

Completed raw observations are immutable.

Corrections shall use one of these mechanisms:

- amendment
- annotation
- derived artifact
- superseding observation
- corrected manifest version

The original observation remains preserved.

Silent in-place editing is prohibited.

---

## 25. Observation Registry

The observation registry records permanent observation identity and high-level
status.

The registry should contain:

- observation ID
- run ID
- experiment ID
- experiment version
- condition ID
- dataset ID
- dataset version
- prompt ID
- prompt version
- subject ID
- model identifier
- status
- created timestamp
- response hash
- cache source observation ID

Large raw responses should not be embedded in the registry.

The registry indexes observation artifacts stored elsewhere.

---

## 26. Observation Directory Layout

Recommended layout:

    observations/
    |
    +-- observation_registry.csv
    +-- observation_registry.json
    |
    +-- EXP-000001/
        |
        +-- RUN-20260725-000001/
            |
            +-- OBS-0000000001/
                |
                +-- observation.json
                +-- request.json
                +-- response.json
                +-- raw_response.txt
                +-- hashes.json
                +-- environment.json
                +-- errors.json
                +-- evaluations/

The registry, raw observations, and derived evaluations should remain logically
separate.

---

## 27. Observation Schema

Every observation JSON artifact must validate against a versioned schema.

The schema should define:

- required fields
- field types
- allowed status values
- identifier formats
- timestamp formats
- nullability
- nested objects
- integrity fields
- extension policy

Schema validation must occur before an observation is accepted as canonical.

---

## 28. Atomic Writes

Observation artifacts must be written atomically where practical.

Recommended procedure:

1. Write to a temporary file.
2. Flush and close the file.
3. Validate the artifact.
4. Calculate the checksum.
5. Rename the temporary file atomically.
6. Update the registry after artifact success.

A partially written observation must never appear as a completed canonical
record.

---

## 29. Concurrency

Future concurrent execution requires safe identifier allocation and registry
updates.

The implementation should support:

- atomic sequence allocation
- file locking or transactional storage
- duplicate-ID prevention
- idempotent retry behavior
- conflict detection
- recovery after interruption

PrimeAIExplorer v0.3 begins with a single-process reference implementation.

---

## 30. Privacy and Security

Observation artifacts shall not contain:

- API keys
- access tokens
- authorization headers
- account passwords
- private credentials
- unnecessary personal data
- undisclosed sensitive information

Request and response logging must apply documented sanitization.

A scientific observatory must preserve evidence without preserving secrets.

---

## 31. Cost Governance

Commercial calls may create financial cost.

Observation records should eventually preserve provider-reported usage and
estimated cost where available.

Cost estimates must identify:

- pricing source
- pricing date
- currency
- input rate
- output rate
- estimation method

Cost data must not be fabricated when unavailable.

PrimeAIExplorer v0.3 uses only dry-run and deterministic local validation.

---

## 32. Deterministic Baseline Observations

The observation layer must support deterministic subjects.

Examples include:

- echo subject
- fixed-response subject
- rule-based subject
- known-answer baseline
- schema validation baseline

These subjects permit complete pipeline testing without external services or
financial cost.

Deterministic baseline observations must be labeled clearly and must not be
represented as frontier-model evidence.

---

## 33. Dry-Run Observations

Dry-run mode may create planned-observation manifests without claiming that a
model execution occurred.

A dry-run record must clearly indicate:

- execution mode: dry_run
- no model call occurred
- no model response was collected
- validation results
- generated prompt hash
- planned subject
- planned configuration

Dry-run artifacts must not be mixed with executed scientific observations.

---

## 34. First Observation Policy

PrimeAIExplorer shall not create its first canonical model observation until:

1. The experiment specification is approved.
2. The dataset release is validated.
3. The prompt release is validated.
4. The observation schema passes.
5. The deterministic baseline passes.
6. The evaluator passes.
7. The statistics pipeline passes.
8. The report pipeline passes.
9. Cache behavior is verified.
10. Paid execution, if any, is explicitly authorized.

This ensures that each model interaction has defined scientific value.

---

## 35. Scientific Safeguards

PrimeAIExplorer observations shall not:

- overwrite raw responses
- conceal failures
- merge retries into one undocumented record
- represent cache reuse as an independent sample
- store credentials
- fabricate token usage
- fabricate model versions
- silently normalize raw evidence
- omit prompt hashes
- omit experimental linkage
- change status without history
- delete inconvenient observations
- claim execution during dry-run mode

---

## 36. Reproducibility Commitment

An observation is scientifically useful only when another researcher can
determine:

- which experiment produced it
- which dataset evidence was visible
- which prompt was rendered
- which subject was contacted
- which parameters were used
- when execution occurred
- what raw response was returned
- how integrity was verified
- whether cache reuse occurred
- how evaluation was performed

PrimeAIExplorer shall preserve this information.

---

## 37. Guiding Statement

Observations are not disposable model outputs.

They are permanent scientific evidence.

Make observations first.

Draw conclusions second.

---

End of Document
'@

Set-Content `
    -Path $CanonicalObservationPath `
    -Value $CanonicalObservation `
    -Encoding UTF8

# ------------------------------------------------------------
# 2. Observation JSON Schema
# ------------------------------------------------------------

$ObservationSchema = [ordered]@{
    '$schema' = "https://json-schema.org/draft/2020-12/schema"
    '$id' = "https://primenet.local/primeaiexplorer/schemas/observation.schema.json"
    title = "PrimeAIExplorer Canonical Observation"
    description = "Canonical schema for a PrimeAIExplorer scientific observation."
    type = "object"
    additionalProperties = $false

    required = @(
        "observation_id",
        "observation_schema_version",
        "run_id",
        "condition_id",
        "attempt_id",
        "status",
        "experiment",
        "dataset",
        "prompt",
        "subject",
        "execution",
        "timing",
        "request",
        "response",
        "integrity",
        "cache",
        "error",
        "environment",
        "evaluation"
    )

    properties = [ordered]@{
        observation_id = [ordered]@{
            type = "string"
            pattern = "^OBS-[0-9]{10}$"
        }

        observation_schema_version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        run_id = [ordered]@{
            type = "string"
            pattern = "^RUN-[0-9]{8}-[0-9]{6}$"
        }

        condition_id = [ordered]@{
            type = "string"
            minLength = 1
        }

        attempt_id = [ordered]@{
            type = "string"
            pattern = "^ATTEMPT-[0-9]{3}$"
        }

        status = [ordered]@{
            type = "string"
            enum = @(
                "pending",
                "executing",
                "succeeded",
                "failed",
                "timed_out",
                "refused",
                "invalid_response",
                "cancelled",
                "cached",
                "superseded"
            )
        }

        experiment = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "experiment_id",
                "experiment_version",
                "experimental_universe"
            )
            properties = [ordered]@{
                experiment_id = [ordered]@{
                    type = "string"
                    pattern = "^EXP-[0-9]{6}$"
                }
                experiment_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                hypothesis_id = [ordered]@{
                    type = @("string", "null")
                }
                experimental_universe = [ordered]@{
                    type = "string"
                    minLength = 1
                }
            }
        }

        dataset = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "dataset_id",
                "dataset_version",
                "partition"
            )
            properties = [ordered]@{
                dataset_id = [ordered]@{
                    type = "string"
                    pattern = "^DS-[0-9]{6}$"
                }
                dataset_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                partition = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                record_id = [ordered]@{
                    type = @("string", "null")
                }
                artifact_sha256 = [ordered]@{
                    type = @("string", "null")
                    pattern = "^[a-fA-F0-9]{64}$"
                }
            }
        }

        prompt = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "prompt_id",
                "prompt_version",
                "rendered_prompt_sha256",
                "response_schema_id"
            )
            properties = [ordered]@{
                prompt_id = [ordered]@{
                    type = "string"
                    pattern = "^PROMPT-[0-9]{6}$"
                }
                prompt_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                rendered_prompt_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
                response_schema_id = [ordered]@{
                    type = "string"
                    pattern = "^RESPONSE-[0-9]{6}$"
                }
                response_schema_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
            }
        }

        subject = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "subject_id",
                "subject_type",
                "provider",
                "connector",
                "model_identifier"
            )
            properties = [ordered]@{
                subject_id = [ordered]@{
                    type = "string"
                    pattern = "^SUBJECT-[0-9]{6}$"
                }
                subject_type = [ordered]@{
                    type = "string"
                    enum = @(
                        "ai_model",
                        "deterministic_baseline",
                        "human",
                        "simulation"
                    )
                }
                provider = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                connector = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                connector_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                model_identifier = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                reported_model_version = [ordered]@{
                    type = @("string", "null")
                }
            }
        }

        execution = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "mode",
                "parameters"
            )
            properties = [ordered]@{
                mode = [ordered]@{
                    type = "string"
                    enum = @(
                        "dry_run",
                        "local",
                        "api",
                        "cached"
                    )
                }
                parameters = [ordered]@{
                    type = "object"
                }
            }
        }

        timing = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "created_at_utc"
            )
            properties = [ordered]@{
                created_at_utc = [ordered]@{
                    type = "string"
                    format = "date-time"
                }
                started_at_utc = [ordered]@{
                    type = @("string", "null")
                    format = "date-time"
                }
                completed_at_utc = [ordered]@{
                    type = @("string", "null")
                    format = "date-time"
                }
                latency_seconds = [ordered]@{
                    type = @("number", "null")
                    minimum = 0
                }
            }
        }

        request = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "request_sha256"
            )
            properties = [ordered]@{
                request_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
                rendered_prompt = [ordered]@{
                    type = @("string", "null")
                }
            }
        }

        response = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "raw_text",
                "response_sha256"
            )
            properties = [ordered]@{
                raw_text = [ordered]@{
                    type = @("string", "null")
                }
                response_sha256 = [ordered]@{
                    type = @("string", "null")
                    pattern = "^[a-fA-F0-9]{64}$"
                }
                finish_reason = [ordered]@{
                    type = @("string", "null")
                }
            }
        }

        integrity = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "algorithm",
                "configuration_sha256"
            )
            properties = [ordered]@{
                algorithm = [ordered]@{
                    type = "string"
                    const = "SHA-256"
                }
                configuration_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
            }
        }

        cache = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "was_cached"
            )
            properties = [ordered]@{
                was_cached = [ordered]@{
                    type = "boolean"
                }
                cache_key = [ordered]@{
                    type = @("string", "null")
                }
                source_observation_id = [ordered]@{
                    type = @("string", "null")
                    pattern = "^OBS-[0-9]{10}$"
                }
            }
        }

        error = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "category",
                "message"
            )
            properties = [ordered]@{
                category = [ordered]@{
                    type = @("string", "null")
                }
                message = [ordered]@{
                    type = @("string", "null")
                }
                retryable = [ordered]@{
                    type = "boolean"
                }
            }
        }

        environment = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "primeaiexplorer_version",
                "python_version",
                "operating_system"
            )
            properties = [ordered]@{
                primeaiexplorer_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                python_version = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                operating_system = [ordered]@{
                    type = "string"
                    minLength = 1
                }
            }
        }

        evaluation = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "state"
            )
            properties = [ordered]@{
                state = [ordered]@{
                    type = "string"
                    enum = @(
                        "not_started",
                        "pending",
                        "valid",
                        "invalid",
                        "scored",
                        "review_required",
                        "reviewed",
                        "excluded_with_reason"
                    )
                }
            }
        }
    }
}

$ObservationSchema |
    ConvertTo-Json -Depth 30 |
    Set-Content `
        -Path $ObservationSchemaPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 3. Empty Canonical Observation Registry
# ------------------------------------------------------------

$RegistryHeader = @(
    "observation_id",
    "run_id",
    "experiment_id",
    "experiment_version",
    "condition_id",
    "dataset_id",
    "dataset_version",
    "prompt_id",
    "prompt_version",
    "subject_id",
    "model_identifier",
    "status",
    "created_at_utc",
    "response_sha256",
    "cache_source_observation_id"
) -join ","

Set-Content `
    -Path $RegistryCsvPath `
    -Value $RegistryHeader `
    -Encoding UTF8

$RegistryObject = [ordered]@{
    registry_name = "PrimeAIExplorer Observation Registry"
    registry_version = "0.3.0"
    observation_schema_version = "0.3.0"
    updated_date = "2026-07-25"
    next_observation_sequence = 1
    observation_count = 0
    observations = @()
}

$RegistryObject |
    ConvertTo-Json -Depth 10 |
    Set-Content `
        -Path $RegistryJsonPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 4. Python Observation Reference Implementation
# ------------------------------------------------------------

$ObservationModule = @'
"""PrimeAIExplorer canonical observation reference implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Mapping


OBSERVATION_SCHEMA_VERSION = "0.3.0"
PRIME_AI_EXPLORER_VERSION = "0.3.0"


class ObservationStatus(StrEnum):
    """Canonical observation lifecycle status."""

    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    REFUSED = "refused"
    INVALID_RESPONSE = "invalid_response"
    CANCELLED = "cancelled"
    CACHED = "cached"
    SUPERSEDED = "superseded"


class EvaluationState(StrEnum):
    """Canonical evaluation state."""

    NOT_STARTED = "not_started"
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    SCORED = "scored"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    EXCLUDED_WITH_REASON = "excluded_with_reason"


def utc_now_iso() -> str:
    """Return a UTC timestamp using a stable ISO 8601 representation."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically for hashing and persistence."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""

    return sha256(value.encode("utf-8")).hexdigest()


def canonical_observation_id(sequence: int) -> str:
    """Convert a positive integer into OBS-NNNNNNNNNN form."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Observation sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Observation sequence must be between 1 and 9,999,999,999."
        )

    return f"OBS-{sequence:010d}"


@dataclass(frozen=True, slots=True)
class ExperimentLink:
    experiment_id: str
    experiment_version: str
    experimental_universe: str
    hypothesis_id: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetLink:
    dataset_id: str
    dataset_version: str
    partition: str
    record_id: str | None = None
    artifact_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class PromptLink:
    prompt_id: str
    prompt_version: str
    rendered_prompt_sha256: str
    response_schema_id: str
    response_schema_version: str


@dataclass(frozen=True, slots=True)
class SubjectLink:
    subject_id: str
    subject_type: str
    provider: str
    connector: str
    connector_version: str
    model_identifier: str
    reported_model_version: str | None = None


@dataclass(slots=True)
class ObservationRecord:
    """Canonical in-memory representation of one observation."""

    observation_id: str
    run_id: str
    condition_id: str
    attempt_id: str
    status: ObservationStatus
    experiment: ExperimentLink
    dataset: DatasetLink
    prompt: PromptLink
    subject: SubjectLink

    observation_schema_version: str = OBSERVATION_SCHEMA_VERSION
    execution: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_dry_run(
        cls,
        *,
        sequence: int,
        run_id: str,
        condition_id: str,
        experiment: ExperimentLink,
        dataset: DatasetLink,
        prompt_id: str,
        prompt_version: str,
        rendered_prompt: str,
        response_schema_id: str,
        response_schema_version: str,
        subject: SubjectLink,
        execution_parameters: Mapping[str, Any] | None = None,
    ) -> "ObservationRecord":
        """Create a planned dry-run observation with no model response."""

        created_at = utc_now_iso()
        prompt_hash = sha256_text(rendered_prompt)

        request_payload = {
            "rendered_prompt": rendered_prompt,
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
        }
        request_hash = sha256_text(canonical_json(request_payload))

        execution = {
            "mode": "dry_run",
            "parameters": dict(execution_parameters or {}),
            "model_call_performed": False,
        }

        configuration_hash = sha256_text(
            canonical_json(
                {
                    "experiment": asdict(experiment),
                    "dataset": asdict(dataset),
                    "prompt_id": prompt_id,
                    "prompt_version": prompt_version,
                    "subject": asdict(subject),
                    "execution": execution,
                }
            )
        )

        return cls(
            observation_id=canonical_observation_id(sequence),
            run_id=run_id,
            condition_id=condition_id,
            attempt_id="ATTEMPT-001",
            status=ObservationStatus.PENDING,
            experiment=experiment,
            dataset=dataset,
            prompt=PromptLink(
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                rendered_prompt_sha256=prompt_hash,
                response_schema_id=response_schema_id,
                response_schema_version=response_schema_version,
            ),
            subject=subject,
            execution=execution,
            timing={
                "created_at_utc": created_at,
                "started_at_utc": None,
                "completed_at_utc": None,
                "latency_seconds": None,
            },
            request={
                "request_sha256": request_hash,
                "rendered_prompt": rendered_prompt,
            },
            response={
                "raw_text": None,
                "response_sha256": None,
                "finish_reason": None,
            },
            integrity={
                "algorithm": "SHA-256",
                "configuration_sha256": configuration_hash,
            },
            cache={
                "was_cached": False,
                "cache_key": None,
                "source_observation_id": None,
            },
            error={
                "category": None,
                "message": None,
                "retryable": False,
            },
            environment={
                "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
                "python_version": platform.python_version(),
                "operating_system": platform.system(),
                "platform": platform.platform(),
            },
            evaluation={
                "state": EvaluationState.NOT_STARTED.value,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible canonical observation dictionary."""

        value = asdict(self)
        value["status"] = self.status.value
        return value

    def to_json(self, *, pretty: bool = True) -> str:
        """Serialize the observation to JSON."""

        if pretty:
            return json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )

        return canonical_json(self.to_dict())

    def write_atomic(self, path: str | Path) -> Path:
        """Write the observation atomically and return the final path."""

        final_path = Path(path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = final_path.with_name(final_path.name + ".tmp")
        payload = self.to_json(pretty=True) + "\n"

        try:
            with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())

            temporary_path.replace(final_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return final_path


__all__ = [
    "DatasetLink",
    "EvaluationState",
    "ExperimentLink",
    "ObservationRecord",
    "ObservationStatus",
    "PromptLink",
    "SubjectLink",
    "canonical_json",
    "canonical_observation_id",
    "sha256_text",
    "utc_now_iso",
]
'@

Set-Content `
    -Path $ObservationModulePath `
    -Value $ObservationModule `
    -Encoding UTF8

if (-not (Test-Path $CoreInitPath)) {
    Set-Content `
        -Path $CoreInitPath `
        -Value '"""PrimeAIExplorer core package."""' `
        -Encoding UTF8
}

# ------------------------------------------------------------
# 5. Python Unit Tests
# ------------------------------------------------------------

$ObservationTests = @'
"""Tests for the PrimeAIExplorer observation foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.observation import (
    DatasetLink,
    ExperimentLink,
    ObservationRecord,
    ObservationStatus,
    SubjectLink,
    canonical_observation_id,
    sha256_text,
)


class CanonicalObservationIdTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(canonical_observation_id(1), "OBS-0000000001")

    def test_larger_identifier(self) -> None:
        self.assertEqual(
            canonical_observation_id(1_234_567),
            "OBS-0001234567",
        )

    def test_zero_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_observation_id(0)

    def test_boolean_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_observation_id(True)


class ObservationRecordTests(unittest.TestCase):
    def build_record(self) -> ObservationRecord:
        rendered_prompt = (
            "Observe the following prime gaps: 2, 4, 2, 4.\n"
            "Return a structured prediction."
        )

        return ObservationRecord.create_dry_run(
            sequence=1,
            run_id="RUN-20260725-000001",
            condition_id="COND-EXP000001-001",
            experiment=ExperimentLink(
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                experimental_universe="PrimeNet",
                hypothesis_id="HYP-EXP-000001-001",
            ),
            dataset=DatasetLink(
                dataset_id="DS-000001",
                dataset_version="0.1.0",
                partition="calibration",
                record_id="REC-DS000001-0000000001",
            ),
            prompt_id="PROMPT-000001",
            prompt_version="0.1.0",
            rendered_prompt=rendered_prompt,
            response_schema_id="RESPONSE-000001",
            response_schema_version="0.1.0",
            subject=SubjectLink(
                subject_id="SUBJECT-000001",
                subject_type="deterministic_baseline",
                provider="PrimeAIExplorer",
                connector="dry_run",
                connector_version="0.3.0",
                model_identifier="no-model-call",
                reported_model_version=None,
            ),
            execution_parameters={
                "temperature": 0,
                "maximum_output_tokens": 128,
            },
        )

    def test_dry_run_does_not_claim_model_execution(self) -> None:
        record = self.build_record()

        self.assertEqual(record.status, ObservationStatus.PENDING)
        self.assertEqual(record.execution["mode"], "dry_run")
        self.assertFalse(record.execution["model_call_performed"])
        self.assertIsNone(record.response["raw_text"])

    def test_prompt_hash_is_stable(self) -> None:
        record = self.build_record()
        expected = sha256_text(
            "Observe the following prime gaps: 2, 4, 2, 4.\n"
            "Return a structured prediction."
        )

        self.assertEqual(
            record.prompt.rendered_prompt_sha256,
            expected,
        )

    def test_json_round_trip(self) -> None:
        record = self.build_record()
        payload = json.loads(record.to_json())

        self.assertEqual(payload["observation_id"], "OBS-0000000001")
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(
            payload["experiment"]["experiment_id"],
            "EXP-000001",
        )

    def test_atomic_write(self) -> None:
        record = self.build_record()

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "observation.json"
            result = record.write_atomic(output)

            self.assertEqual(result, output)
            self.assertTrue(output.exists())
            self.assertFalse(
                output.with_name(output.name + ".tmp").exists()
            )

            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                saved["observation_id"],
                "OBS-0000000001",
            )


if __name__ == "__main__":
    unittest.main()
'@

Set-Content `
    -Path $ObservationTestPath `
    -Value $ObservationTests `
    -Encoding UTF8

# ------------------------------------------------------------
# 6. Version and Changelog
# ------------------------------------------------------------

Set-Content `
    -Path $VersionPath `
    -Value "0.3.0" `
    -Encoding UTF8

$ChangelogEntry = @'
# PrimeAIExplorer Changelog

## 0.3.0 - 2026-07-25

### Added

- Canonical Observation Specification.
- Canonical observation JSON Schema.
- Empty canonical observation registries in CSV and JSON.
- Python observation reference implementation.
- Atomic observation writing.
- Deterministic observation identifiers.
- Dry-run observation construction.
- Observation integrity hashing.
- Observation unit tests.
- Observation status and evaluation-state enumerations.

### Scientific policy

Every execution attempt is treated as a permanent scientific observation.

Raw evidence is preserved independently from derived evaluation artifacts.

Dry-run records must never claim that a model call occurred.

## 0.2.0 - 2026-07-25

### Added

- Scientific Principles.
- Canonical Experiment Specification.
- Canonical Dataset Specification.
- Canonical Prompt Specification.
- Experiment, dataset, and prompt registries.
'@

Set-Content `
    -Path $ChangelogPath `
    -Value $ChangelogEntry `
    -Encoding UTF8

# ------------------------------------------------------------
# 7. Validation
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.3"
Write-Host " Observation Foundation"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

$RequiredFiles = @(
    $CanonicalObservationPath,
    $ObservationSchemaPath,
    $RegistryCsvPath,
    $RegistryJsonPath,
    $ObservationModulePath,
    $CoreInitPath,
    $ObservationTestPath,
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
    "PrimeAIExplorer Canonical Observation Specification",
    "OBS-NNNNNNNNNN",
    "Every completed execution attempt shall create an observation record.",
    "Cache reuse must not create the appearance of a new independent model sample.",
    "Observations are not disposable model outputs.",
    "Make observations first.",
    "Draw conclusions second."
)

$DocumentContent = Get-Content $CanonicalObservationPath -Raw

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
    $Schema = Get-Content $ObservationSchemaPath -Raw |
        ConvertFrom-Json

    if ($Schema.title -eq "PrimeAIExplorer Canonical Observation") {
        Write-Host "[PASS] Observation schema JSON is valid"
    }
    else {
        Write-Host "[FAIL] Unexpected observation schema title"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Observation schema JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

try {
    $Registry = Get-Content $RegistryJsonPath -Raw |
        ConvertFrom-Json

    if (
        $Registry.observation_count -eq 0 -and
        $Registry.next_observation_sequence -eq 1
    ) {
        Write-Host "[PASS] Observation registry initialized correctly"
    }
    else {
        Write-Host "[FAIL] Observation registry state is unexpected"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Observation registry JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

$Version = (Get-Content $VersionPath -Raw).Trim()

if ($Version -eq "0.3.0") {
    Write-Host "[PASS] VERSION is 0.3.0"
}
else {
    Write-Host "[FAIL] VERSION is not 0.3.0"
    $Failed = $true
}

Write-Host ""
Write-Host "Python compilation:"

Push-Location $Root

try {
    py -m compileall `
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
    Write-Host "Python tests:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_observation.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Observation tests failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Observation tests passed"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Canonical observation document line count:"

$LineCount = (Get-Content $CanonicalObservationPath).Count
Write-Host $LineCount

if ($LineCount -lt 300) {
    Write-Host "[WARN] Canonical observation document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "PRIMEAIEXPLORER v0.3 FAILED"
    exit 1
}

Write-Host ""
Write-Host "PRIMEAIEXPLORER v0.3 PASSED"