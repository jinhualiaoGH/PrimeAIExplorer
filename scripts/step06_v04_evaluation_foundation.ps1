# ============================================================
# PrimeAIExplorer v0.4
# Step 6 - Evaluation Foundation
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"

$ArchitectureDir = Join-Path $Root "architecture"
$SchemasDir      = Join-Path $Root "schemas"
$EvaluationsDir  = Join-Path $Root "evaluations"
$CoreDir         = Join-Path $Root "core"
$TestsDir        = Join-Path $Root "tests"

$CanonicalEvaluationPath = Join-Path $ArchitectureDir "Canonical_Evaluation.md"
$EvaluationSchemaPath    = Join-Path $SchemasDir "evaluation.schema.json"
$RegistryCsvPath         = Join-Path $EvaluationsDir "evaluation_registry.csv"
$RegistryJsonPath        = Join-Path $EvaluationsDir "evaluation_registry.json"
$EvaluationModulePath    = Join-Path $CoreDir "evaluation.py"
$EvaluationTestPath      = Join-Path $TestsDir "test_evaluation.py"
$CoreInitPath            = Join-Path $CoreDir "__init__.py"
$VersionPath             = Join-Path $Root "VERSION"
$ChangelogPath           = Join-Path $Root "CHANGELOG.md"

$RequiredDirectories = @(
    $ArchitectureDir,
    $SchemasDir,
    $EvaluationsDir,
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
# 1. Canonical Evaluation Specification
# ------------------------------------------------------------

$CanonicalEvaluation = @'
# PrimeAIExplorer Canonical Evaluation Specification

Version: 0.4.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of scientific evaluation
within PrimeAIExplorer.

Evaluation transforms preserved observations into explicit measurements.

Evaluation does not replace raw evidence.

Every evaluation result must remain traceable to the exact observation,
evaluator, metric definition, configuration, and software version that
produced it.

---

## 2. Foundational Principle

Raw observations and derived evaluations are separate scientific objects.

An observation records what happened.

An evaluation records how that observation was measured.

Evaluation shall never silently rewrite, normalize, delete, or replace raw
observation evidence.

---

## 3. Evaluator Identifier

Every reusable evaluator receives a permanent identifier:

EVAL-NNNNNN

Examples:

- EVAL-000001
- EVAL-000002
- EVAL-000125

Rules:

- Evaluator identifiers are permanent.
- Evaluator identifiers shall never be reused.
- Evaluator revisions use semantic versions.
- Materially different scoring methods receive different evaluator IDs.
- Retired evaluators remain preserved in the registry.

---

## 4. Evaluation Result Identifier

Every generated evaluation result receives a permanent identifier:

EVR-NNNNNNNNNN

Examples:

- EVR-0000000001
- EVR-0000000002
- EVR-0000123456

An evaluation result identifier identifies one immutable application of an
evaluator to one observation under one declared configuration.

---

## 5. Evaluation Lifecycle

Permitted evaluation statuses include:

- pending
- running
- valid
- invalid
- scored
- review_required
- reviewed
- failed
- excluded_with_reason
- superseded

### pending

The evaluation record has been allocated but processing has not started.

### running

Evaluation is currently in progress.

### valid

The response satisfies the applicable structural contract.

### invalid

The response does not satisfy the applicable structural contract.

### scored

One or more metric values have been generated.

### review_required

Automated evaluation cannot determine the result reliably.

### reviewed

A documented human or independent review has been completed.

### failed

Evaluation ended because of a technical or evaluator error.

### excluded_with_reason

The result is excluded from a declared analysis for an explicit reason.

### superseded

The original evaluation remains preserved but a documented replacement exists.

---

## 6. Canonical Evaluation Structure

Every evaluation result shall contain:

- identity
- observation linkage
- experiment linkage
- evaluator linkage
- evaluation configuration
- validity assessment
- metric results
- uncertainty
- review state
- exclusions
- integrity
- environment
- provenance
- governance

---

## 7. Identity

Required identity fields include:

- evaluation_result_id
- evaluation_schema_version
- status
- created_at_utc
- started_at_utc
- completed_at_utc

All timestamps shall use UTC and ISO 8601 formatting.

---

## 8. Observation Linkage

Every evaluation result must reference:

- observation ID
- observation schema version
- response hash
- prompt hash
- experiment ID
- dataset ID
- prompt ID
- subject ID
- run ID
- condition ID

The evaluator must verify that referenced evidence matches the recorded hashes
where practical.

---

## 9. Evaluator Linkage

Every result must reference:

- evaluator ID
- evaluator version
- evaluator name
- evaluator type
- implementation version
- configuration hash

Evaluator types may include:

- deterministic
- rule_based
- statistical
- rubric_based
- human_review
- model_based
- composite

Deterministic evaluators are preferred whenever the scientific task permits
objective measurement.

---

## 10. Primary and Secondary Metrics

Every experiment should declare one primary metric before confirmatory
observations are interpreted.

Additional metrics may be classified as:

- primary
- secondary
- diagnostic
- exploratory
- quality_control

The metric role must be recorded with every metric result.

Post-hoc metric selection must be disclosed.

---

## 11. Metric Identifier

Every reusable metric should have a canonical identifier:

METRIC-NNNNNN

Examples:

- METRIC-000001
- METRIC-000002
- METRIC-000003

A metric definition shall document:

- name
- scientific meaning
- input requirements
- output type
- valid range
- unit
- direction of improvement
- missing-value policy
- invalid-response policy
- aggregation policy

---

## 12. Initial Canonical Metrics

PrimeAIExplorer v0.4 defines the following initial metrics.

### METRIC-000001 — Exact Match Accuracy

Measures whether normalized predicted text exactly equals normalized expected
text.

Output:

- 1.0 for a match
- 0.0 for a non-match

Normalization must be explicitly configured and versioned.

### METRIC-000002 — Numeric Absolute Error

Measures the absolute difference between a predicted numeric value and expected
numeric value.

Formula:

absolute_error = absolute_value(prediction - expected)

Lower values are better.

### METRIC-000003 — Numeric Relative Error

Measures numeric error relative to the magnitude of the expected value.

The zero-target policy must be documented.

### METRIC-000004 — Response Validity

Measures whether the response satisfies the expected response contract.

Output:

- 1.0 for valid
- 0.0 for invalid

### METRIC-000005 — Abstention Indicator

Records whether the subject explicitly abstained or declined to answer.

This metric describes behavior and is not automatically interpreted as good or
bad.

---

## 13. Validity Before Scoring

Response validity should be evaluated before task correctness.

Validity checks may include:

- required response present
- valid JSON
- required fields present
- field types correct
- numeric values finite
- labels belong to permitted set
- no unresolved template content
- response satisfies declared schema

Invalid responses must remain preserved.

The invalid-response scoring policy must be defined before analysis.

---

## 14. Exact-Match Evaluation

Exact-match evaluation must define normalization.

Possible normalization operations include:

- Unicode normalization
- line-ending normalization
- trimming leading and trailing whitespace
- collapsing internal whitespace
- case folding
- punctuation handling

Default PrimeAIExplorer behavior shall be conservative.

No semantic equivalence shall be inferred by exact-match evaluation.

---

## 15. Numeric Evaluation

Numeric evaluation must document:

- parser
- accepted numeric formats
- decimal precision
- scientific notation policy
- units
- tolerance
- absolute error
- relative error
- overflow handling
- non-finite-value handling

Numbers shall not be silently rounded before evaluation unless the metric
definition explicitly requires it.

---

## 16. Tolerance Policies

A numeric correctness metric may use:

- exact equality
- absolute tolerance
- relative tolerance
- combined absolute and relative tolerance
- interval containment

The tolerance policy must be declared before primary analysis.

Changing tolerance after observing results constitutes an evaluation amendment.

---

## 17. Structured-Response Evaluation

Structured responses should be validated against a versioned schema.

The evaluator should preserve:

- raw response
- parsing result
- parser errors
- schema errors
- extracted fields
- normalized representation
- validity state

Parsing failure does not erase the response.

---

## 18. Missing and Invalid Data

The evaluation specification must distinguish:

- missing response
- empty response
- malformed response
- refused response
- timed-out response
- provider failure
- parser failure
- valid but incorrect response

These categories must not be collapsed silently into one generic error.

---

## 19. Abstention

An abstention may be explicit or inferred under a declared rule.

Examples include:

- "I do not know"
- "Insufficient information"
- a structured abstain field set to true

The abstention detector must be versioned.

Abstention must not automatically be treated as correct or incorrect unless the
experiment defines that policy.

---

## 20. Deterministic Evaluators

A deterministic evaluator should produce the same result from identical inputs
and configuration.

Deterministic evaluators must define:

- input canonicalization
- evaluation algorithm
- configuration
- software version
- output schema
- error behavior

Deterministic evaluation is the default foundation for PrimeAIExplorer v0.4.

---

## 21. Rubric-Based Evaluation

Some capabilities cannot be evaluated fully by exact deterministic metrics.

Rubric-based evaluation may be used for:

- explanation quality
- abstraction quality
- hypothesis quality
- scientific reasoning
- conceptual transfer

Every rubric must define:

- dimensions
- score levels
- examples
- prohibited criteria
- uncertainty policy
- review policy
- agreement procedure

Rubric-based results must be labeled separately from objective ground-truth
metrics.

---

## 22. Model-Based Evaluation

A model may eventually be used as an evaluator, but such evaluation must be
treated as another experimental process.

Model-based evaluation must record:

- evaluator model
- evaluator prompt
- evaluator parameters
- repetitions
- disagreement
- calibration
- bias risks
- cost
- raw evaluator responses

PrimeAIExplorer v0.4 does not require external model-based evaluation.

---

## 23. Human Review

Human review may be used when automated evaluation is insufficient.

A human-review record should capture:

- reviewer identifier or blinded code
- rubric version
- review timestamp
- score
- rationale
- confidence
- conflicts
- adjudication

Personally identifying information should be minimized.

---

## 24. Uncertainty

Evaluation results may include uncertainty.

Potential uncertainty representations include:

- confidence interval
- standard error
- probability
- score range
- reviewer disagreement
- parser ambiguity
- calibration interval

Uncertainty values must identify their derivation method.

---

## 25. Exclusions

An observation may be excluded from a particular analysis only for a documented
reason.

Potential reasons include:

- experiment configuration violation
- corrupted artifact
- duplicate execution
- unauthorized prompt change
- evaluator defect
- known leakage
- unsupported response type

Exclusion does not delete the observation or evaluation record.

---

## 26. Evaluation Immutability

Completed evaluation results are immutable.

Corrections require:

1. A new evaluation result.
2. A new evaluator version when appropriate.
3. A documented amendment.
4. Preservation of the original result.
5. An explicit supersession link.

Silent in-place score editing is prohibited.

---

## 27. Evaluation Registry

The evaluation registry catalogs reusable evaluator definitions.

The registry should contain:

- evaluator ID
- title
- short name
- version
- status
- evaluator type
- primary metric ID
- implementation module
- created date
- modified date

Large result records shall not be stored directly in the evaluator registry.

---

## 28. Evaluation Result Storage

Recommended layout:

    evaluations/
    |
    +-- evaluation_registry.csv
    +-- evaluation_registry.json
    |
    +-- EXP-000001/
        |
        +-- RUN-20260725-000001/
            |
            +-- OBS-0000000001/
                |
                +-- EVR-0000000001.json
                +-- metrics.json
                +-- validation.json
                +-- review.json
                +-- hashes.json

Raw observations remain under the observation layer.

---

## 29. Evaluation Schema

Every evaluation-result artifact must validate against a versioned schema.

The schema should define:

- identifier formats
- required fields
- permitted statuses
- metric-result representation
- nullability
- timestamps
- integrity fields
- provenance fields
- extension policy

Schema validation is required before an evaluation result is accepted as
canonical.

---

## 30. Atomic Writes

Evaluation artifacts shall be written atomically where practical.

Recommended sequence:

1. Write a temporary artifact.
2. Flush and close it.
3. Validate the artifact.
4. Calculate its checksum.
5. Rename it atomically.
6. Update indexes after success.

Partially written files must not appear as completed scientific results.

---

## 31. Evaluation Environment

Each result should record:

- PrimeAIExplorer version
- Python version
- operating system
- evaluator implementation version
- parser version
- schema version
- dependency versions
- source-control commit when available

Environment capture must support reproduction without unnecessarily exposing
private machine information.

---

## 32. Evaluation Integrity

Potential hashes include:

- source observation hash
- evaluator configuration hash
- metric-definition hash
- evaluation result hash
- normalized-response hash
- expected-answer hash

SHA-256 is the default integrity algorithm.

Expected-answer values may require restricted storage in hidden-evaluation
campaigns.

---

## 33. Leakage Protection

Evaluation infrastructure must not leak hidden answers into model prompts.

Expected values, scoring keys, and evaluator rules must remain separated from
model-visible prompt content.

Logs and reports generated before model execution must not expose hidden
evaluation targets.

---

## 34. Free Development Policy

The evaluation layer must be fully testable without paid model access.

PrimeAIExplorer v0.4 supports:

- deterministic unit tests
- synthetic observations
- exact-match evaluation
- numeric-error evaluation
- structured-response validation
- atomic result writing
- integrity hashing

No API cost is required.

---

## 35. First Canonical Evaluators

PrimeAIExplorer v0.4 registers:

### EVAL-000001

Exact Match Evaluator

Primary metric:

METRIC-000001

### EVAL-000002

Numeric Error Evaluator

Primary metric:

METRIC-000002

### EVAL-000003

 Structured Response Validity Evaluator

Primary metric:

METRIC-000004

These evaluators provide the initial objective evaluation foundation for
EXP-000001.

---

## 36. Scientific Safeguards

PrimeAIExplorer evaluations shall not:

- overwrite raw observations
- conceal invalid responses
- change scoring rules silently
- select metrics after observing outcomes without disclosure
- fabricate missing expected answers
- fabricate confidence values
- treat model consensus as mathematical ground truth
- remove inconvenient scores
- hide exclusions
- combine incompatible evaluator versions silently
- claim semantic equivalence through exact-match scoring
- store hidden answers in model-visible prompt artifacts

---

## 37. Reproducibility Commitment

An evaluation result is scientifically useful only when another researcher can
determine:

- which observation was evaluated
- which evaluator was used
- which evaluator version was used
- which configuration was applied
- which expected answer was used
- how normalization occurred
- which metric values were produced
- why a result was invalid or excluded
- how integrity was verified

PrimeAIExplorer shall preserve this information.

---

## 38. Guiding Statement

Evaluation is not a replacement for observation.

It is a documented measurement derived from preserved evidence.

Make observations first.

Draw conclusions second.

---

End of Document
'@

Set-Content `
    -Path $CanonicalEvaluationPath `
    -Value $CanonicalEvaluation `
    -Encoding UTF8

# ------------------------------------------------------------
# 2. Evaluation JSON Schema
# ------------------------------------------------------------

$EvaluationSchema = [ordered]@{
    '$schema' = "https://json-schema.org/draft/2020-12/schema"
    '$id' = "https://primenet.local/primeaiexplorer/schemas/evaluation.schema.json"
    title = "PrimeAIExplorer Canonical Evaluation Result"
    description = "Canonical schema for a PrimeAIExplorer evaluation result."
    type = "object"
    additionalProperties = $false

    required = @(
        "evaluation_result_id",
        "evaluation_schema_version",
        "status",
        "created_at_utc",
        "observation",
        "evaluator",
        "configuration",
        "validity",
        "metrics",
        "review",
        "exclusion",
        "integrity",
        "environment",
        "provenance"
    )

    properties = [ordered]@{
        evaluation_result_id = [ordered]@{
            type = "string"
            pattern = "^EVR-[0-9]{10}$"
        }

        evaluation_schema_version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        status = [ordered]@{
            type = "string"
            enum = @(
                "pending",
                "running",
                "valid",
                "invalid",
                "scored",
                "review_required",
                "reviewed",
                "failed",
                "excluded_with_reason",
                "superseded"
            )
        }

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

        observation = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "observation_id",
                "observation_schema_version",
                "response_sha256"
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
                response_sha256 = [ordered]@{
                    type = @("string", "null")
                    pattern = "^[a-fA-F0-9]{64}$"
                }
            }
        }

        evaluator = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "evaluator_id",
                "evaluator_version",
                "name",
                "evaluator_type",
                "implementation_version"
            )
            properties = [ordered]@{
                evaluator_id = [ordered]@{
                    type = "string"
                    pattern = "^EVAL-[0-9]{6}$"
                }
                evaluator_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                name = [ordered]@{
                    type = "string"
                    minLength = 1
                }
                evaluator_type = [ordered]@{
                    type = "string"
                    enum = @(
                        "deterministic",
                        "rule_based",
                        "statistical",
                        "rubric_based",
                        "human_review",
                        "model_based",
                        "composite"
                    )
                }
                implementation_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
            }
        }

        configuration = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "configuration_sha256"
            )
            properties = [ordered]@{
                configuration_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
            }
        }

        validity = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "is_valid",
                "reason"
            )
            properties = [ordered]@{
                is_valid = [ordered]@{
                    type = "boolean"
                }
                reason = [ordered]@{
                    type = @("string", "null")
                }
            }
        }

        metrics = [ordered]@{
            type = "array"
            items = [ordered]@{
                type = "object"
                additionalProperties = $false
                required = @(
                    "metric_id",
                    "name",
                    "role",
                    "value",
                    "unit",
                    "higher_is_better",
                    "status"
                )
                properties = [ordered]@{
                    metric_id = [ordered]@{
                        type = "string"
                        pattern = "^METRIC-[0-9]{6}$"
                    }
                    name = [ordered]@{
                        type = "string"
                        minLength = 1
                    }
                    role = [ordered]@{
                        type = "string"
                        enum = @(
                            "primary",
                            "secondary",
                            "diagnostic",
                            "exploratory",
                            "quality_control"
                        )
                    }
                    value = [ordered]@{
                        type = @("number", "integer", "string", "boolean", "null")
                    }
                    unit = [ordered]@{
                        type = @("string", "null")
                    }
                    higher_is_better = [ordered]@{
                        type = @("boolean", "null")
                    }
                    status = [ordered]@{
                        type = "string"
                        enum = @(
                            "computed",
                            "not_applicable",
                            "invalid_input",
                            "failed"
                        )
                    }
                    details = [ordered]@{
                        type = "object"
                    }
                }
            }
        }

        review = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "required",
                "completed"
            )
            properties = [ordered]@{
                required = [ordered]@{
                    type = "boolean"
                }
                completed = [ordered]@{
                    type = "boolean"
                }
            }
        }

        exclusion = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "excluded",
                "reason"
            )
            properties = [ordered]@{
                excluded = [ordered]@{
                    type = "boolean"
                }
                reason = [ordered]@{
                    type = @("string", "null")
                }
            }
        }

        integrity = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "algorithm",
                "result_sha256"
            )
            properties = [ordered]@{
                algorithm = [ordered]@{
                    type = "string"
                    const = "SHA-256"
                }
                result_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
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

        provenance = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "source_observation_id",
                "evaluation_timestamp_utc"
            )
            properties = [ordered]@{
                source_observation_id = [ordered]@{
                    type = "string"
                    pattern = "^OBS-[0-9]{10}$"
                }
                evaluation_timestamp_utc = [ordered]@{
                    type = "string"
                    format = "date-time"
                }
            }
        }
    }
}

$EvaluationSchema |
    ConvertTo-Json -Depth 30 |
    Set-Content `
        -Path $EvaluationSchemaPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 3. Evaluation Registry
# ------------------------------------------------------------

$RegistryRows = @(
    [pscustomobject][ordered]@{
        evaluator_id         = "EVAL-000001"
        title                = "Exact Match Evaluator"
        short_name           = "exact_match"
        version              = "0.1.0"
        status               = "Active"
        evaluator_type       = "deterministic"
        primary_metric_id    = "METRIC-000001"
        implementation_module = "core.evaluation"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        evaluator_id         = "EVAL-000002"
        title                = "Numeric Error Evaluator"
        short_name           = "numeric_error"
        version              = "0.1.0"
        status               = "Active"
        evaluator_type       = "deterministic"
        primary_metric_id    = "METRIC-000002"
        implementation_module = "core.evaluation"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        evaluator_id         = "EVAL-000003"
        title                = "Structured Response Validity Evaluator"
        short_name           = "structured_response_validity"
        version              = "0.1.0"
        status               = "Active"
        evaluator_type       = "deterministic"
        primary_metric_id    = "METRIC-000004"
        implementation_module = "core.evaluation"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    }
)

$RegistryRows |
    Export-Csv `
        -Path $RegistryCsvPath `
        -NoTypeInformation `
        -Encoding UTF8

$RegistryObject = [ordered]@{
    registry_name = "PrimeAIExplorer Evaluation Registry"
    registry_version = "0.4.0"
    evaluation_schema_version = "0.4.0"
    updated_date = "2026-07-25"
    evaluators = @(
        foreach ($Row in $RegistryRows) {
            [ordered]@{
                evaluator_id          = $Row.evaluator_id
                title                 = $Row.title
                short_name            = $Row.short_name
                version               = $Row.version
                status                = $Row.status
                evaluator_type        = $Row.evaluator_type
                primary_metric_id     = $Row.primary_metric_id
                implementation_module = $Row.implementation_module
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
# 4. Python Evaluation Reference Implementation
# ------------------------------------------------------------

$EvaluationModule = @'
"""PrimeAIExplorer canonical evaluation reference implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import re
from typing import Any, Iterable, Mapping
import unicodedata


EVALUATION_SCHEMA_VERSION = "0.4.0"
PRIME_AI_EXPLORER_VERSION = "0.4.0"
EVALUATOR_IMPLEMENTATION_VERSION = "0.4.0"


class EvaluationStatus(StrEnum):
    """Canonical evaluation lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    VALID = "valid"
    INVALID = "invalid"
    SCORED = "scored"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    FAILED = "failed"
    EXCLUDED_WITH_REASON = "excluded_with_reason"
    SUPERSEDED = "superseded"


class MetricStatus(StrEnum):
    """Canonical metric-computation status."""

    COMPUTED = "computed"
    NOT_APPLICABLE = "not_applicable"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class MetricRole(StrEnum):
    """Scientific role of a metric."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DIAGNOSTIC = "diagnostic"
    EXPLORATORY = "exploratory"
    QUALITY_CONTROL = "quality_control"


def utc_now_iso() -> str:
    """Return a stable UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically."""

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


def canonical_evaluation_result_id(sequence: int) -> str:
    """Convert a positive integer to EVR-NNNNNNNNNN form."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Evaluation-result sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Evaluation-result sequence must be between 1 and 9,999,999,999."
        )

    return f"EVR-{sequence:010d}"


def normalize_text(
    value: str,
    *,
    strip: bool = True,
    casefold: bool = False,
    collapse_whitespace: bool = False,
    unicode_form: str = "NFC",
) -> str:
    """Normalize text under an explicit deterministic policy."""

    if not isinstance(value, str):
        raise TypeError("Text normalization requires a string.")

    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = unicodedata.normalize(unicode_form, normalized)

    if strip:
        normalized = normalized.strip()

    if collapse_whitespace:
        normalized = re.sub(r"\s+", " ", normalized)

    if casefold:
        normalized = normalized.casefold()

    return normalized


def parse_decimal(value: Any) -> Decimal:
    """Parse a finite numeric value into Decimal."""

    if isinstance(value, bool):
        raise TypeError("Boolean values are not numeric predictions.")

    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Numeric values must be finite.")
        result = Decimal(str(value))
    elif isinstance(value, str):
        text = value.strip()

        if not text:
            raise ValueError("Numeric text is empty.")

        try:
            result = Decimal(text)
        except InvalidOperation as error:
            raise ValueError(f"Invalid numeric value: {value!r}") from error
    else:
        raise TypeError(
            "Numeric values must be int, float, Decimal, or numeric text."
        )

    if not result.is_finite():
        raise ValueError("Numeric values must be finite.")

    return result


@dataclass(frozen=True, slots=True)
class MetricResult:
    """One canonical metric result."""

    metric_id: str
    name: str
    role: MetricRole
    value: int | float | str | bool | None
    unit: str | None
    higher_is_better: bool | None
    status: MetricStatus = MetricStatus.COMPUTED
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["role"] = self.role.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class EvaluationRecord:
    """Canonical evaluation result derived from one observation."""

    evaluation_result_id: str
    status: EvaluationStatus
    created_at_utc: str
    observation: dict[str, Any]
    evaluator: dict[str, Any]
    configuration: dict[str, Any]
    validity: dict[str, Any]
    metrics: list[MetricResult]

    evaluation_schema_version: str = EVALUATION_SCHEMA_VERSION
    started_at_utc: str | None = None
    completed_at_utc: str | None = None
    review: dict[str, Any] = field(default_factory=dict)
    exclusion: dict[str, Any] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_result_hash: bool = True) -> dict[str, Any]:
        value = {
            "evaluation_result_id": self.evaluation_result_id,
            "evaluation_schema_version": self.evaluation_schema_version,
            "status": self.status.value,
            "created_at_utc": self.created_at_utc,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "observation": dict(self.observation),
            "evaluator": dict(self.evaluator),
            "configuration": dict(self.configuration),
            "validity": dict(self.validity),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "review": dict(self.review),
            "exclusion": dict(self.exclusion),
            "integrity": dict(self.integrity),
            "environment": dict(self.environment),
            "provenance": dict(self.provenance),
        }

        if not include_result_hash:
            value["integrity"] = {
                key: item
                for key, item in value["integrity"].items()
                if key != "result_sha256"
            }

        return value

    def finalize_integrity(self) -> None:
        """Calculate a stable hash without recursively hashing itself."""

        payload = canonical_json(
            self.to_dict(include_result_hash=False)
        )

        self.integrity["algorithm"] = "SHA-256"
        self.integrity["result_sha256"] = sha256_text(payload)

    def to_json(self, *, pretty: bool = True) -> str:
        if not self.integrity.get("result_sha256"):
            self.finalize_integrity()

        value = self.to_dict()

        if pretty:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )

        return canonical_json(value)

    def write_atomic(self, path: str | Path) -> Path:
        """Write the evaluation atomically."""

        final_path = Path(path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = final_path.with_name(final_path.name + ".tmp")
        payload = self.to_json(pretty=True) + "\n"

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


def _base_record(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    evaluator_id: str,
    evaluator_version: str,
    evaluator_name: str,
    configuration: Mapping[str, Any],
    validity: Mapping[str, Any],
    metrics: Iterable[MetricResult],
) -> EvaluationRecord:
    timestamp = utc_now_iso()
    configuration_value = dict(configuration)
    configuration_hash = sha256_text(
        canonical_json(configuration_value)
    )

    record = EvaluationRecord(
        evaluation_result_id=canonical_evaluation_result_id(sequence),
        status=EvaluationStatus.SCORED,
        created_at_utc=timestamp,
        started_at_utc=timestamp,
        completed_at_utc=timestamp,
        observation={
            "observation_id": observation_id,
            "observation_schema_version": observation_schema_version,
            "response_sha256": response_sha256,
        },
        evaluator={
            "evaluator_id": evaluator_id,
            "evaluator_version": evaluator_version,
            "name": evaluator_name,
            "evaluator_type": "deterministic",
            "implementation_version": EVALUATOR_IMPLEMENTATION_VERSION,
        },
        configuration={
            **configuration_value,
            "configuration_sha256": configuration_hash,
        },
        validity=dict(validity),
        metrics=list(metrics),
        review={
            "required": False,
            "completed": False,
        },
        exclusion={
            "excluded": False,
            "reason": None,
        },
        integrity={
            "algorithm": "SHA-256",
            "result_sha256": "",
        },
        environment={
            "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        },
        provenance={
            "source_observation_id": observation_id,
            "evaluation_timestamp_utc": timestamp,
        },
    )

    record.finalize_integrity()
    return record


def evaluate_exact_match(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    prediction: str,
    expected: str,
    casefold: bool = False,
    collapse_whitespace: bool = False,
) -> EvaluationRecord:
    """Evaluate normalized exact textual equality."""

    normalized_prediction = normalize_text(
        prediction,
        casefold=casefold,
        collapse_whitespace=collapse_whitespace,
    )
    normalized_expected = normalize_text(
        expected,
        casefold=casefold,
        collapse_whitespace=collapse_whitespace,
    )

    matched = normalized_prediction == normalized_expected

    metric = MetricResult(
        metric_id="METRIC-000001",
        name="exact_match_accuracy",
        role=MetricRole.PRIMARY,
        value=1.0 if matched else 0.0,
        unit="proportion",
        higher_is_better=True,
        details={
            "matched": matched,
            "normalized_prediction_sha256": sha256_text(
                normalized_prediction
            ),
            "normalized_expected_sha256": sha256_text(
                normalized_expected
            ),
        },
    )

    return _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000001",
        evaluator_version="0.1.0",
        evaluator_name="Exact Match Evaluator",
        configuration={
            "strip": True,
            "unicode_form": "NFC",
            "casefold": casefold,
            "collapse_whitespace": collapse_whitespace,
        },
        validity={
            "is_valid": True,
            "reason": None,
        },
        metrics=[metric],
    )


def evaluate_numeric_error(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    prediction: Any,
    expected: Any,
) -> EvaluationRecord:
    """Evaluate absolute and relative numeric error."""

    predicted_value = parse_decimal(prediction)
    expected_value = parse_decimal(expected)

    absolute_error = abs(predicted_value - expected_value)

    if expected_value == 0:
        relative_error: Decimal | None = (
            Decimal(0) if absolute_error == 0 else None
        )
        relative_status = (
            MetricStatus.COMPUTED
            if relative_error is not None
            else MetricStatus.NOT_APPLICABLE
        )
    else:
        relative_error = absolute_error / abs(expected_value)
        relative_status = MetricStatus.COMPUTED

    absolute_metric = MetricResult(
        metric_id="METRIC-000002",
        name="numeric_absolute_error",
        role=MetricRole.PRIMARY,
        value=float(absolute_error),
        unit=None,
        higher_is_better=False,
        details={
            "prediction": str(predicted_value),
            "expected": str(expected_value),
        },
    )

    relative_metric = MetricResult(
        metric_id="METRIC-000003",
        name="numeric_relative_error",
        role=MetricRole.SECONDARY,
        value=(
            float(relative_error)
            if relative_error is not None
            else None
        ),
        unit="proportion",
        higher_is_better=False,
        status=relative_status,
        details={
            "zero_target_policy": (
                "zero_when_exact_otherwise_not_applicable"
            ),
        },
    )

    return _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000002",
        evaluator_version="0.1.0",
        evaluator_name="Numeric Error Evaluator",
        configuration={
            "parser": "decimal",
            "finite_values_required": True,
            "zero_target_policy": (
                "zero_when_exact_otherwise_not_applicable"
            ),
        },
        validity={
            "is_valid": True,
            "reason": None,
        },
        metrics=[absolute_metric, relative_metric],
    )


def evaluate_required_json_fields(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    raw_text: str,
    required_fields: Iterable[str],
) -> EvaluationRecord:
    """Validate that JSON text is an object with required fields."""

    fields = tuple(required_fields)
    parsed: Any = None
    reason: str | None = None
    is_valid = False

    try:
        parsed = json.loads(raw_text)

        if not isinstance(parsed, dict):
            reason = "Response JSON must be an object."
        else:
            missing = [
                field_name
                for field_name in fields
                if field_name not in parsed
            ]

            if missing:
                reason = (
                    "Missing required fields: "
                    + ", ".join(sorted(missing))
                )
            else:
                is_valid = True
    except json.JSONDecodeError as error:
        reason = (
            f"Invalid JSON at line {error.lineno}, "
            f"column {error.colno}."
        )

    metric = MetricResult(
        metric_id="METRIC-000004",
        name="response_validity",
        role=MetricRole.QUALITY_CONTROL,
        value=1.0 if is_valid else 0.0,
        unit="proportion",
        higher_is_better=True,
        details={
            "required_fields": list(fields),
            "parsed_type": (
                type(parsed).__name__
                if parsed is not None
                else None
            ),
        },
    )

    record = _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000003",
        evaluator_version="0.1.0",
        evaluator_name="Structured Response Validity Evaluator",
        configuration={
            "required_fields": list(fields),
            "root_type": "object",
        },
        validity={
            "is_valid": is_valid,
            "reason": reason,
        },
        metrics=[metric],
    )

    record.status = (
        EvaluationStatus.SCORED
        if is_valid
        else EvaluationStatus.INVALID
    )
    record.finalize_integrity()
    return record


__all__ = [
    "EvaluationRecord",
    "EvaluationStatus",
    "MetricResult",
    "MetricRole",
    "MetricStatus",
    "canonical_evaluation_result_id",
    "canonical_json",
    "evaluate_exact_match",
    "evaluate_numeric_error",
    "evaluate_required_json_fields",
    "normalize_text",
    "parse_decimal",
    "sha256_text",
    "utc_now_iso",
]
'@

Set-Content `
    -Path $EvaluationModulePath `
    -Value $EvaluationModule `
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

$EvaluationTests = @'
"""Tests for the PrimeAIExplorer evaluation foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.evaluation import (
    EvaluationStatus,
    MetricStatus,
    canonical_evaluation_result_id,
    evaluate_exact_match,
    evaluate_numeric_error,
    evaluate_required_json_fields,
    normalize_text,
    parse_decimal,
)


OBSERVATION_ID = "OBS-0000000001"
OBSERVATION_SCHEMA_VERSION = "0.3.0"
RESPONSE_HASH = "a" * 64


class EvaluationIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_evaluation_result_id(1),
            "EVR-0000000001",
        )

    def test_large_identifier(self) -> None:
        self.assertEqual(
            canonical_evaluation_result_id(1_234_567),
            "EVR-0001234567",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_evaluation_result_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_evaluation_result_id(True)


class NormalizationTests(unittest.TestCase):
    def test_default_normalization(self) -> None:
        self.assertEqual(
            normalize_text("  PrimeNet\r\n"),
            "PrimeNet",
        )

    def test_casefold_and_whitespace(self) -> None:
        self.assertEqual(
            normalize_text(
                "  PRIME   NET ",
                casefold=True,
                collapse_whitespace=True,
            ),
            "prime net",
        )


class NumericParsingTests(unittest.TestCase):
    def test_integer(self) -> None:
        self.assertEqual(str(parse_decimal(42)), "42")

    def test_numeric_text(self) -> None:
        self.assertEqual(str(parse_decimal("1.25")), "1.25")

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            parse_decimal(True)

    def test_non_finite_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_decimal(float("inf"))


class ExactMatchEvaluationTests(unittest.TestCase):
    def test_exact_match(self) -> None:
        result = evaluate_exact_match(
            sequence=1,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="PrimeNet",
            expected="PrimeNet",
        )

        self.assertEqual(result.status, EvaluationStatus.SCORED)
        self.assertEqual(result.metrics[0].value, 1.0)
        self.assertTrue(result.metrics[0].details["matched"])

    def test_casefold_match(self) -> None:
        result = evaluate_exact_match(
            sequence=2,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="PRIMENET",
            expected="primenet",
            casefold=True,
        )

        self.assertEqual(result.metrics[0].value, 1.0)

    def test_non_match(self) -> None:
        result = evaluate_exact_match(
            sequence=3,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="2",
            expected="4",
        )

        self.assertEqual(result.metrics[0].value, 0.0)


class NumericEvaluationTests(unittest.TestCase):
    def test_absolute_and_relative_error(self) -> None:
        result = evaluate_numeric_error(
            sequence=4,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="12",
            expected="10",
        )

        self.assertEqual(result.metrics[0].value, 2.0)
        self.assertAlmostEqual(result.metrics[1].value, 0.2)

    def test_zero_target_nonzero_prediction(self) -> None:
        result = evaluate_numeric_error(
            sequence=5,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="1",
            expected="0",
        )

        self.assertIsNone(result.metrics[1].value)
        self.assertEqual(
            result.metrics[1].status,
            MetricStatus.NOT_APPLICABLE,
        )


class StructuredValidityTests(unittest.TestCase):
    def test_valid_json_object(self) -> None:
        result = evaluate_required_json_fields(
            sequence=6,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text='{"prediction": 6, "confidence": 0.8}',
            required_fields=("prediction", "confidence"),
        )

        self.assertEqual(result.status, EvaluationStatus.SCORED)
        self.assertTrue(result.validity["is_valid"])
        self.assertEqual(result.metrics[0].value, 1.0)

    def test_missing_field(self) -> None:
        result = evaluate_required_json_fields(
            sequence=7,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text='{"prediction": 6}',
            required_fields=("prediction", "confidence"),
        )

        self.assertEqual(result.status, EvaluationStatus.INVALID)
        self.assertFalse(result.validity["is_valid"])
        self.assertIn("confidence", result.validity["reason"])

    def test_invalid_json(self) -> None:
        result = evaluate_required_json_fields(
            sequence=8,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            raw_text="{not-json}",
            required_fields=("prediction",),
        )

        self.assertEqual(result.status, EvaluationStatus.INVALID)
        self.assertEqual(result.metrics[0].value, 0.0)


class EvaluationPersistenceTests(unittest.TestCase):
    def test_result_hash_is_stable(self) -> None:
        result = evaluate_exact_match(
            sequence=9,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        first_hash = result.integrity["result_sha256"]
        result.finalize_integrity()
        second_hash = result.integrity["result_sha256"]

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_json_round_trip(self) -> None:
        result = evaluate_exact_match(
            sequence=10,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        payload = json.loads(result.to_json())

        self.assertEqual(
            payload["evaluation_result_id"],
            "EVR-0000000010",
        )
        self.assertEqual(payload["status"], "scored")
        self.assertEqual(
            payload["observation"]["observation_id"],
            OBSERVATION_ID,
        )

    def test_atomic_write(self) -> None:
        result = evaluate_exact_match(
            sequence=11,
            observation_id=OBSERVATION_ID,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            response_sha256=RESPONSE_HASH,
            prediction="6",
            expected="6",
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evaluation.json"
            saved_path = result.write_atomic(output)

            self.assertEqual(saved_path, output)
            self.assertTrue(output.exists())
            self.assertFalse(
                output.with_name(output.name + ".tmp").exists()
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["evaluation_result_id"],
                "EVR-0000000011",
            )


if __name__ == "__main__":
    unittest.main()
'@

Set-Content `
    -Path $EvaluationTestPath `
    -Value $EvaluationTests `
    -Encoding UTF8

# ------------------------------------------------------------
# 6. Version and Changelog
# ------------------------------------------------------------

Set-Content `
    -Path $VersionPath `
    -Value "0.4.0" `
    -Encoding UTF8

$NewChangelogSection = @'
## 0.4.0 - 2026-07-25

### Added

- Canonical Evaluation Specification.
- Canonical evaluation-result JSON Schema.
- Evaluation registry in CSV and JSON.
- Exact-match evaluator.
- Numeric absolute-error evaluator.
- Numeric relative-error metric.
- Structured-response validity evaluator.
- Deterministic text normalization.
- Decimal-based numeric parsing.
- Atomic evaluation-result writing.
- Evaluation integrity hashing.
- Evaluation unit tests.

### Scientific policy

Raw observations and derived evaluations are separate immutable scientific
objects.

Evaluation methods and primary metrics should be defined before confirmatory
results are interpreted.

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

if ($ExistingBody -notmatch "(?m)^## 0\.4\.0 - 2026-07-25") {
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
# 7. Validation
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.4"
Write-Host " Evaluation Foundation"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

$RequiredFiles = @(
    $CanonicalEvaluationPath,
    $EvaluationSchemaPath,
    $RegistryCsvPath,
    $RegistryJsonPath,
    $EvaluationModulePath,
    $EvaluationTestPath,
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
    "PrimeAIExplorer Canonical Evaluation Specification",
    "EVAL-NNNNNN",
    "EVR-NNNNNNNNNN",
    "Raw observations and derived evaluations are separate scientific objects.",
    "Validity Before Scoring",
    "Exact Match Evaluator",
    "Numeric Error Evaluator",
    "Evaluation is not a replacement for observation.",
    "Make observations first.",
    "Draw conclusions second."
)

$DocumentContent = Get-Content $CanonicalEvaluationPath -Raw

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
    $Schema = Get-Content $EvaluationSchemaPath -Raw |
        ConvertFrom-Json

    if (
        $Schema.title -eq
        "PrimeAIExplorer Canonical Evaluation Result"
    ) {
        Write-Host "[PASS] Evaluation schema JSON is valid"
    }
    else {
        Write-Host "[FAIL] Unexpected evaluation schema title"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Evaluation schema JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

try {
    $RegistryJson = Get-Content $RegistryJsonPath -Raw |
        ConvertFrom-Json

    if ($RegistryJson.evaluators.Count -eq 3) {
        Write-Host "[PASS] Evaluation registry contains 3 evaluators"
    }
    else {
        Write-Host "[FAIL] Unexpected evaluator count"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Evaluation registry JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

$CsvRows = @(
    Import-Csv $RegistryCsvPath
)

if ($CsvRows.Count -eq 3) {
    Write-Host "[PASS] Evaluation registry CSV contains 3 evaluators"
}
else {
    Write-Host "[FAIL] Unexpected evaluator CSV count"
    $Failed = $true
}

$DuplicateIds = @(
    $CsvRows |
        Group-Object evaluator_id |
        Where-Object Count -gt 1
)

if ($DuplicateIds.Count -eq 0) {
    Write-Host "[PASS] No duplicate evaluator identifiers"
}
else {
    Write-Host "[FAIL] Duplicate evaluator identifiers detected"
    $Failed = $true
}

$InvalidEvaluatorIds = @(
    $CsvRows |
        Where-Object {
            $_.evaluator_id -notmatch "^EVAL-[0-9]{6}$"
        }
)

if ($InvalidEvaluatorIds.Count -eq 0) {
    Write-Host "[PASS] All evaluator identifiers are canonical"
}
else {
    Write-Host "[FAIL] Invalid evaluator identifiers detected"
    $Failed = $true
}

$InvalidMetricIds = @(
    $CsvRows |
        Where-Object {
            $_.primary_metric_id -notmatch "^METRIC-[0-9]{6}$"
        }
)

if ($InvalidMetricIds.Count -eq 0) {
    Write-Host "[PASS] All primary metric identifiers are canonical"
}
else {
    Write-Host "[FAIL] Invalid primary metric identifiers detected"
    $Failed = $true
}

$Version = (Get-Content $VersionPath -Raw).Trim()

if ($Version -eq "0.4.0") {
    Write-Host "[PASS] VERSION is 0.4.0"
}
else {
    Write-Host "[FAIL] VERSION is not 0.4.0"
    $Failed = $true
}

Write-Host ""
Write-Host "Evaluation registry:"

$CsvRows |
    Format-Table `
        evaluator_id,
        title,
        version,
        evaluator_type,
        primary_metric_id `
        -AutoSize

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
    Write-Host "Evaluation tests:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_evaluation.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Evaluation tests failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Evaluation tests passed"
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
Write-Host "Canonical evaluation document line count:"

$LineCount = (Get-Content $CanonicalEvaluationPath).Count
Write-Host $LineCount

if ($LineCount -lt 300) {
    Write-Host "[WARN] Canonical evaluation document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "PRIMEAIEXPLORER v0.4 FAILED"
    exit 1
}

Write-Host ""
Write-Host "PRIMEAIEXPLORER v0.4 PASSED"