# ============================================================
# PrimeAIExplorer v0.6
# Step 8 - Scientific Report Foundation
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"

$ArchitectureDir = Join-Path $Root "architecture"
$SchemasDir      = Join-Path $Root "schemas"
$ReportsDir      = Join-Path $Root "reports"
$CoreDir         = Join-Path $Root "core"
$TestsDir        = Join-Path $Root "tests"

$CanonicalReportPath = Join-Path $ArchitectureDir "Canonical_Report.md"
$ReportSchemaPath    = Join-Path $SchemasDir "scientific_report.schema.json"
$RegistryCsvPath     = Join-Path $ReportsDir "report_registry.csv"
$RegistryJsonPath    = Join-Path $ReportsDir "report_registry.json"
$ReportModulePath    = Join-Path $CoreDir "report.py"
$ReportTestPath      = Join-Path $TestsDir "test_report.py"
$CoreInitPath        = Join-Path $CoreDir "__init__.py"
$VersionPath         = Join-Path $Root "VERSION"
$ChangelogPath       = Join-Path $Root "CHANGELOG.md"

$RequiredDirectories = @(
    $ArchitectureDir,
    $SchemasDir,
    $ReportsDir,
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
# 1. Canonical Report Specification
# ------------------------------------------------------------

$CanonicalReport = @'
# PrimeAIExplorer Canonical Scientific Report Specification

Version: 0.6.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of scientific reports
within PrimeAIExplorer.

A scientific report communicates preserved evidence, declared measurements,
statistical summaries, uncertainty, limitations, and interpretations.

Reports do not replace the underlying observations, evaluations, or
statistical artifacts.

Every reported claim must remain traceable to its supporting scientific
objects.

---

## 2. Scientific Object Hierarchy

PrimeAIExplorer distinguishes:

1. Experiment specification
2. Dataset
3. Prompt
4. Observation
5. Evaluation
6. Statistical summary
7. Scientific report
8. Scientific interpretation

A report presents evidence.

It does not manufacture evidence.

---

## 3. Foundational Principle

Claims must remain proportional to evidence.

Reports shall clearly distinguish:

- direct observation
- objective evaluation
- statistical summary
- scientific interpretation
- hypothesis
- limitation
- unresolved question

Interpretation must not be presented as raw observation.

---

## 4. Report Definition Identifier

Every reusable report definition receives a permanent identifier:

REPORT-NNNNNN

Examples:

- REPORT-000001
- REPORT-000002
- REPORT-000125

Identifiers are permanent and shall never be reused.

Report-definition revisions use semantic versioning.

---

## 5. Report Artifact Identifier

Every generated scientific report receives a permanent identifier:

RPT-NNNNNNNNNN

Examples:

- RPT-0000000001
- RPT-0000000002
- RPT-0000123456

A report artifact identifies one immutable report generated from one declared
evidence manifest and one report configuration.

---

## 6. Report Lifecycle

Permitted statuses include:

- draft
- generated
- validation
- review_required
- reviewed
- approved
- released
- superseded
- withdrawn

A released report shall never be silently edited.

Corrections require a new report artifact or documented amendment.

---

## 7. Canonical Report Structure

Every scientific report should contain:

- identity
- title
- abstract or executive summary
- scientific question
- hypothesis
- experimental scope
- methods
- dataset provenance
- prompt and execution protocol
- observation accounting
- evaluation methods
- statistical methods
- results
- uncertainty
- limitations
- interpretation
- conclusions
- reproducibility
- evidence manifest
- integrity
- governance

---

## 8. Identity

Required identity fields include:

- report_artifact_id
- report_schema_version
- report_definition_id
- report_definition_version
- status
- created_at_utc
- generated_at_utc
- title
- authors
- experiment ID
- experiment version

---

## 9. Evidence Manifest

Every report must reference its evidence through an immutable manifest.

The manifest may include:

- observation IDs
- evaluation-result IDs
- statistical-summary IDs
- dataset IDs and versions
- prompt IDs and versions
- run IDs
- condition IDs
- artifact hashes

The evidence manifest itself shall have a cryptographic checksum.

---

## 10. Observation Accounting

The report must state:

- planned observations
- attempted observations
- successful observations
- failed observations
- timed-out observations
- refused observations
- invalid responses
- cached references
- original executions
- excluded observations

Cache reuse must not appear as an independent model sample.

---

## 11. Evaluation Reporting

Reports shall identify:

- evaluator IDs
- evaluator versions
- metric IDs
- primary metric
- secondary metrics
- normalization policies
- invalid-response policies
- exclusion policies
- human-review procedures where applicable

Evaluation methods must not be described more precisely than the implementation
supports.

---

## 12. Statistical Reporting

Reports should state:

- unit of analysis
- sample size
- missingness
- descriptive statistics
- uncertainty method
- confidence level
- condition comparisons
- outlier policy
- retry policy
- cache policy
- exploratory or confirmatory role

Confidence intervals and descriptive differences must not be presented as
causal proof.

---

## 13. Results and Interpretation

Results and interpretation shall be separated.

### Results

Reports measurements and statistical summaries.

### Interpretation

Discusses what the evidence may mean.

Interpretation must identify uncertainty and alternative explanations.

---

## 14. Negative and Null Results

Reports shall preserve scientifically meaningful:

- null effects
- failed hypotheses
- inconsistent behavior
- non-monotonic trends
- refusals
- invalid responses
- saturation
- regressions
- unexpected results

Selective reporting is prohibited.

---

## 15. Limitations

Every scientific report must include limitations.

Potential limitations include:

- limited model sample
- unknown provider revision
- nondeterminism
- small sample size
- prompt sensitivity
- dataset scope
- distribution shift
- evaluator limitations
- missing usage data
- context-window constraints
- lack of independent replication

---

## 16. Reproducibility

A report should reference:

- PrimeAIExplorer version
- source-control commit
- experiment version
- dataset versions and checksums
- prompt versions and hashes
- observation manifests
- evaluator versions
- statistical-analysis versions
- environment information
- report-generator version

---

## 17. Supported Formats

PrimeAIExplorer v0.6 supports canonical generation of:

- Markdown scientific reports
- JSON report manifests

Future versions may support:

- HTML
- PDF
- DOCX
- LaTeX
- publication packages

The Markdown and JSON artifacts remain the initial canonical forms.

---

## 18. Deterministic Generation

Report generation should be deterministic when the same:

- report definition
- evidence manifest
- section data
- software version
- rendering configuration

are supplied.

Dynamic timestamps must be recorded separately from scientific content hashes
when appropriate.

---

## 19. Report Integrity

SHA-256 is the default integrity algorithm.

Potential hashes include:

- evidence-manifest hash
- report-configuration hash
- Markdown report hash
- JSON manifest hash
- result-table hash
- figure-manifest hash

A changed evidence source must change the evidence-manifest checksum.

---

## 20. Atomic Writes

Report artifacts shall be written atomically.

Recommended sequence:

1. Render into memory.
2. Write a temporary artifact.
3. Flush and close it.
4. Validate it.
5. Compute its checksum.
6. Rename it atomically.
7. Update the registry after success.

---

## 21. Report Registry

The report registry catalogs reusable report definitions.

Initial fields include:

- report-definition ID
- title
- short name
- version
- status
- report type
- primary experiment
- implementation module
- created date
- modified date

Generated report artifacts are stored separately.

---

## 22. Initial Report Definitions

PrimeAIExplorer v0.6 registers:

### REPORT-000001 — Experiment Scientific Report

Produces a complete experiment-level scientific report.

### REPORT-000002 — Run Validation Report

Reports execution, integrity, failure, and evidence-preservation status.

### REPORT-000003 — Condition Comparison Report

Reports measurements and descriptive comparisons between experimental
conditions.

---

## 23. Directory Layout

Recommended layout:

    reports/
    |
    +-- report_registry.csv
    +-- report_registry.json
    |
    +-- EXP-000001/
        |
        +-- RPT-0000000001/
            |
            +-- scientific_report.md
            +-- report_manifest.json
            +-- evidence_manifest.json
            +-- checksums.json

---

## 24. Scientific Safeguards

PrimeAIExplorer reports shall not:

- omit failed observations selectively
- count cached responses as new independent samples
- conceal missing data
- alter metric definitions silently
- present interpretation as direct observation
- claim causation from descriptive comparisons
- report unsupported precision
- fabricate uncertainty
- fabricate model versions
- hide exclusions
- overwrite released reports
- disconnect claims from their evidence

---

## 25. Free Development Policy

The report layer must be testable without paid model access.

PrimeAIExplorer v0.6 supports:

- synthetic report data
- deterministic Markdown generation
- JSON report manifests
- evidence-manifest hashing
- atomic report writing
- section validation
- report integrity tests

No external API calls are required.

---

## 26. Reproducibility Commitment

A scientific report is useful only when another researcher can determine:

- which experiment was reported
- which evidence was included
- which evidence was excluded
- which evaluators and metrics were used
- which statistics were calculated
- which limitations were identified
- which statements are observations
- which statements are interpretations
- how the report was generated
- how integrity was verified

PrimeAIExplorer shall preserve this information.

---

## 27. Guiding Statement

Reports communicate evidence.

They do not replace evidence.

Make observations first.

Evaluate transparently.

Summarize reproducibly.

Report honestly.

Draw conclusions second.

---

End of Document
'@

Set-Content `
    -Path $CanonicalReportPath `
    -Value $CanonicalReport `
    -Encoding UTF8

# ------------------------------------------------------------
# 2. Report JSON Schema
# ------------------------------------------------------------

$ReportSchema = [ordered]@{
    '$schema' = "https://json-schema.org/draft/2020-12/schema"
    '$id' = "https://primenet.local/primeaiexplorer/schemas/scientific_report.schema.json"
    title = "PrimeAIExplorer Canonical Scientific Report"
    description = "Canonical schema for a PrimeAIExplorer report manifest."
    type = "object"
    additionalProperties = $false

    required = @(
        "report_artifact_id",
        "report_schema_version",
        "report_definition",
        "status",
        "created_at_utc",
        "title",
        "authors",
        "experiment",
        "sections",
        "evidence",
        "integrity",
        "environment",
        "provenance"
    )

    properties = [ordered]@{
        report_artifact_id = [ordered]@{
            type = "string"
            pattern = "^RPT-[0-9]{10}$"
        }

        report_schema_version = [ordered]@{
            type = "string"
            pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
        }

        report_definition = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "report_definition_id",
                "report_definition_version",
                "report_type"
            )
            properties = [ordered]@{
                report_definition_id = [ordered]@{
                    type = "string"
                    pattern = "^REPORT-[0-9]{6}$"
                }
                report_definition_version = [ordered]@{
                    type = "string"
                    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
                }
                report_type = [ordered]@{
                    type = "string"
                    minLength = 1
                }
            }
        }

        status = [ordered]@{
            type = "string"
            enum = @(
                "draft",
                "generated",
                "validation",
                "review_required",
                "reviewed",
                "approved",
                "released",
                "superseded",
                "withdrawn"
            )
        }

        created_at_utc = [ordered]@{
            type = "string"
            format = "date-time"
        }

        title = [ordered]@{
            type = "string"
            minLength = 1
        }

        authors = [ordered]@{
            type = "array"
            items = [ordered]@{
                type = "string"
                minLength = 1
            }
        }

        experiment = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "experiment_id",
                "experiment_version"
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
            }
        }

        sections = [ordered]@{
            type = "array"
            minItems = 1
            items = [ordered]@{
                type = "object"
                additionalProperties = $false
                required = @(
                    "section_id",
                    "title",
                    "content"
                )
                properties = [ordered]@{
                    section_id = [ordered]@{
                        type = "string"
                        minLength = 1
                    }
                    title = [ordered]@{
                        type = "string"
                        minLength = 1
                    }
                    content = [ordered]@{
                        type = "string"
                    }
                }
            }
        }

        evidence = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "observation_ids",
                "evaluation_result_ids",
                "statistical_summary_ids",
                "evidence_manifest_sha256"
            )
            properties = [ordered]@{
                observation_ids = [ordered]@{
                    type = "array"
                    items = [ordered]@{
                        type = "string"
                        pattern = "^OBS-[0-9]{10}$"
                    }
                }
                evaluation_result_ids = [ordered]@{
                    type = "array"
                    items = [ordered]@{
                        type = "string"
                        pattern = "^EVR-[0-9]{10}$"
                    }
                }
                statistical_summary_ids = [ordered]@{
                    type = "array"
                    items = [ordered]@{
                        type = "string"
                        pattern = "^SSR-[0-9]{10}$"
                    }
                }
                evidence_manifest_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
            }
        }

        integrity = [ordered]@{
            type = "object"
            additionalProperties = $false
            required = @(
                "algorithm",
                "report_manifest_sha256",
                "markdown_sha256"
            )
            properties = [ordered]@{
                algorithm = [ordered]@{
                    type = "string"
                    const = "SHA-256"
                }
                report_manifest_sha256 = [ordered]@{
                    type = "string"
                    pattern = "^[a-fA-F0-9]{64}$"
                }
                markdown_sha256 = [ordered]@{
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
                }
                python_version = [ordered]@{
                    type = "string"
                }
                operating_system = [ordered]@{
                    type = "string"
                }
            }
        }

        provenance = [ordered]@{
            type = "object"
            additionalProperties = $true
            required = @(
                "generated_at_utc",
                "generator_version"
            )
            properties = [ordered]@{
                generated_at_utc = [ordered]@{
                    type = "string"
                    format = "date-time"
                }
                generator_version = [ordered]@{
                    type = "string"
                }
            }
        }
    }
}

$ReportSchema |
    ConvertTo-Json -Depth 30 |
    Set-Content `
        -Path $ReportSchemaPath `
        -Encoding UTF8

# ------------------------------------------------------------
# 3. Report Registry
# ------------------------------------------------------------

$RegistryRows = @(
    [pscustomobject][ordered]@{
        report_definition_id = "REPORT-000001"
        title                = "Experiment Scientific Report"
        short_name           = "experiment_scientific_report"
        version              = "0.1.0"
        status               = "Active"
        report_type          = "experiment"
        primary_experiment   = "EXP-000001"
        implementation_module = "core.report"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        report_definition_id = "REPORT-000002"
        title                = "Run Validation Report"
        short_name           = "run_validation_report"
        version              = "0.1.0"
        status               = "Active"
        report_type          = "validation"
        primary_experiment   = "EXP-000001"
        implementation_module = "core.report"
        created_date         = "2026-07-25"
        modified_date        = "2026-07-25"
    },
    [pscustomobject][ordered]@{
        report_definition_id = "REPORT-000003"
        title                = "Condition Comparison Report"
        short_name           = "condition_comparison_report"
        version              = "0.1.0"
        status               = "Active"
        report_type          = "comparison"
        primary_experiment   = "EXP-000001"
        implementation_module = "core.report"
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
    registry_name = "PrimeAIExplorer Report Registry"
    registry_version = "0.6.0"
    report_schema_version = "0.6.0"
    updated_date = "2026-07-25"
    report_definitions = @(
        foreach ($Row in $RegistryRows) {
            [ordered]@{
                report_definition_id  = $Row.report_definition_id
                title                 = $Row.title
                short_name            = $Row.short_name
                version               = $Row.version
                status                = $Row.status
                report_type           = $Row.report_type
                primary_experiment    = $Row.primary_experiment
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
# 4. Python Report Implementation
# ------------------------------------------------------------

$ReportModule = @'
"""PrimeAIExplorer canonical scientific report implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping, Sequence


REPORT_SCHEMA_VERSION = "0.6.0"
PRIME_AI_EXPLORER_VERSION = "0.6.0"
REPORT_GENERATOR_VERSION = "0.6.0"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATION = "validation"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    RELEASED = "released"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


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


def canonical_report_artifact_id(sequence: int) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Report sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Report sequence must be between 1 and 9,999,999,999."
        )

    return f"RPT-{sequence:010d}"


@dataclass(frozen=True, slots=True)
class ReportSection:
    section_id: str
    title: str
    content: str

    def __post_init__(self) -> None:
        if not self.section_id.strip():
            raise ValueError("Section ID cannot be empty.")

        if not self.title.strip():
            raise ValueError("Section title cannot be empty.")

    def to_dict(self) -> dict[str, str]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
        }


@dataclass(slots=True)
class ScientificReport:
    report_artifact_id: str
    report_definition: dict[str, Any]
    status: ReportStatus
    created_at_utc: str
    title: str
    authors: list[str]
    experiment: dict[str, str]
    sections: list[ReportSection]
    evidence: dict[str, Any]

    report_schema_version: str = REPORT_SCHEMA_VERSION
    integrity: dict[str, str] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def render_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Report ID: {self.report_artifact_id}",
            f"Status: {self.status.value}",
            (
                "Experiment: "
                f"{self.experiment['experiment_id']} "
                f"v{self.experiment['experiment_version']}"
            ),
            "",
        ]

        if self.authors:
            lines.extend(
                [
                    "Authors: " + ", ".join(self.authors),
                    "",
                ]
            )

        for section in self.sections:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                    section.content.rstrip(),
                    "",
                ]
            )

        lines.extend(
            [
                "## Evidence",
                "",
                (
                    "Observations: "
                    f"{len(self.evidence['observation_ids'])}"
                ),
                (
                    "Evaluation results: "
                    f"{len(self.evidence['evaluation_result_ids'])}"
                ),
                (
                    "Statistical summaries: "
                    f"{len(self.evidence['statistical_summary_ids'])}"
                ),
                "",
                "Make observations first.",
                "",
                "Draw conclusions second.",
                "",
            ]
        )

        return "\n".join(lines)

    def to_dict(
        self,
        *,
        include_manifest_hash: bool = True,
    ) -> dict[str, Any]:
        value = {
            "report_artifact_id": self.report_artifact_id,
            "report_schema_version": self.report_schema_version,
            "report_definition": dict(self.report_definition),
            "status": self.status.value,
            "created_at_utc": self.created_at_utc,
            "title": self.title,
            "authors": list(self.authors),
            "experiment": dict(self.experiment),
            "sections": [
                section.to_dict()
                for section in self.sections
            ],
            "evidence": dict(self.evidence),
            "integrity": dict(self.integrity),
            "environment": dict(self.environment),
            "provenance": dict(self.provenance),
        }

        if not include_manifest_hash:
            value["integrity"] = {
                key: item
                for key, item in value["integrity"].items()
                if key != "report_manifest_sha256"
            }

        return value

    def finalize_integrity(self) -> None:
        markdown = self.render_markdown()

        self.integrity["algorithm"] = "SHA-256"
        self.integrity["markdown_sha256"] = sha256_text(markdown)

        manifest_payload = canonical_json(
            self.to_dict(include_manifest_hash=False)
        )

        self.integrity["report_manifest_sha256"] = sha256_text(
            manifest_payload
        )

    def to_json(self, *, pretty: bool = True) -> str:
        if not self.integrity.get("report_manifest_sha256"):
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

    def write_atomic(self, directory: str | Path) -> dict[str, Path]:
        output_directory = Path(directory)
        output_directory.mkdir(parents=True, exist_ok=True)

        self.finalize_integrity()

        markdown_path = output_directory / "scientific_report.md"
        manifest_path = output_directory / "report_manifest.json"

        artifacts = {
            markdown_path: self.render_markdown() + "\n",
            manifest_path: self.to_json(pretty=True) + "\n",
        }

        temporary_paths: list[Path] = []

        try:
            for final_path, payload in artifacts.items():
                temporary_path = final_path.with_name(
                    final_path.name + ".tmp"
                )
                temporary_paths.append(temporary_path)

                with temporary_path.open(
                    "w",
                    encoding="utf-8",
                    newline="\n",
                ) as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())

            for final_path in artifacts:
                temporary_path = final_path.with_name(
                    final_path.name + ".tmp"
                )
                temporary_path.replace(final_path)
        except Exception:
            for temporary_path in temporary_paths:
                temporary_path.unlink(missing_ok=True)
            raise

        return {
            "markdown": markdown_path,
            "manifest": manifest_path,
        }


def build_experiment_report(
    *,
    sequence: int,
    title: str,
    authors: Sequence[str],
    experiment_id: str,
    experiment_version: str,
    sections: Iterable[ReportSection],
    observation_ids: Iterable[str],
    evaluation_result_ids: Iterable[str],
    statistical_summary_ids: Iterable[str],
) -> ScientificReport:
    section_list = list(sections)

    if not section_list:
        raise ValueError("At least one report section is required.")

    observation_list = list(observation_ids)
    evaluation_list = list(evaluation_result_ids)
    statistical_list = list(statistical_summary_ids)

    evidence_payload = {
        "observation_ids": observation_list,
        "evaluation_result_ids": evaluation_list,
        "statistical_summary_ids": statistical_list,
    }

    timestamp = utc_now_iso()

    report = ScientificReport(
        report_artifact_id=canonical_report_artifact_id(sequence),
        report_definition={
            "report_definition_id": "REPORT-000001",
            "report_definition_version": "0.1.0",
            "report_type": "experiment",
        },
        status=ReportStatus.GENERATED,
        created_at_utc=timestamp,
        title=title,
        authors=list(authors),
        experiment={
            "experiment_id": experiment_id,
            "experiment_version": experiment_version,
        },
        sections=section_list,
        evidence={
            **evidence_payload,
            "evidence_manifest_sha256": sha256_text(
                canonical_json(evidence_payload)
            ),
        },
        integrity={
            "algorithm": "SHA-256",
            "report_manifest_sha256": "",
            "markdown_sha256": "",
        },
        environment={
            "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        },
        provenance={
            "generated_at_utc": timestamp,
            "generator_version": REPORT_GENERATOR_VERSION,
        },
    )

    report.finalize_integrity()
    return report


__all__ = [
    "ReportSection",
    "ReportStatus",
    "ScientificReport",
    "build_experiment_report",
    "canonical_json",
    "canonical_report_artifact_id",
    "sha256_text",
    "utc_now_iso",
]
'@

Set-Content `
    -Path $ReportModulePath `
    -Value $ReportModule `
    -Encoding UTF8

if (-not (Test-Path $CoreInitPath)) {
    Set-Content `
        -Path $CoreInitPath `
        -Value '"""PrimeAIExplorer core package."""' `
        -Encoding UTF8
}

# ------------------------------------------------------------
# 5. Unit Tests
# ------------------------------------------------------------

$ReportTests = @'
"""Tests for the PrimeAIExplorer report foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.report import (
    ReportSection,
    ReportStatus,
    build_experiment_report,
    canonical_report_artifact_id,
)


class ReportIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_report_artifact_id(1),
            "RPT-0000000001",
        )

    def test_larger_identifier(self) -> None:
        self.assertEqual(
            canonical_report_artifact_id(1_234_567),
            "RPT-0001234567",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_report_artifact_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_report_artifact_id(True)


class ReportSectionTests(unittest.TestCase):
    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ReportSection(
                section_id="results",
                title="",
                content="Evidence.",
            )


class ScientificReportTests(unittest.TestCase):
    def build_report(self):
        return build_experiment_report(
            sequence=1,
            title="EXP-000001 Pilot Scientific Report",
            authors=["Jinhua Liao"],
            experiment_id="EXP-000001",
            experiment_version="0.1.0",
            sections=[
                ReportSection(
                    section_id="scientific_question",
                    title="Scientific Question",
                    content=(
                        "How does observational memory influence "
                        "generalization?"
                    ),
                ),
                ReportSection(
                    section_id="results",
                    title="Results",
                    content=(
                        "This synthetic report validates the "
                        "report-generation pipeline."
                    ),
                ),
                ReportSection(
                    section_id="limitations",
                    title="Limitations",
                    content=(
                        "No external model call was performed."
                    ),
                ),
            ],
            observation_ids=[
                "OBS-0000000001",
                "OBS-0000000002",
            ],
            evaluation_result_ids=[
                "EVR-0000000001",
                "EVR-0000000002",
            ],
            statistical_summary_ids=[
                "SSR-0000000001",
            ],
        )

    def test_report_identity(self) -> None:
        report = self.build_report()

        self.assertEqual(
            report.report_artifact_id,
            "RPT-0000000001",
        )
        self.assertEqual(
            report.status,
            ReportStatus.GENERATED,
        )

    def test_markdown_rendering(self) -> None:
        report = self.build_report()
        markdown = report.render_markdown()

        self.assertIn(
            "# EXP-000001 Pilot Scientific Report",
            markdown,
        )
        self.assertIn("## Results", markdown)
        self.assertIn("Observations: 2", markdown)
        self.assertIn(
            "Draw conclusions second.",
            markdown,
        )

    def test_evidence_hash_is_stable(self) -> None:
        report = self.build_report()

        first_hash = report.evidence[
            "evidence_manifest_sha256"
        ]

        second_report = self.build_report()
        second_hash = second_report.evidence[
            "evidence_manifest_sha256"
        ]

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_report_hash_is_stable_after_refinalize(self) -> None:
        report = self.build_report()

        first_manifest_hash = report.integrity[
            "report_manifest_sha256"
        ]
        first_markdown_hash = report.integrity[
            "markdown_sha256"
        ]

        report.finalize_integrity()

        self.assertEqual(
            first_manifest_hash,
            report.integrity["report_manifest_sha256"],
        )
        self.assertEqual(
            first_markdown_hash,
            report.integrity["markdown_sha256"],
        )

    def test_json_round_trip(self) -> None:
        report = self.build_report()
        payload = json.loads(report.to_json())

        self.assertEqual(
            payload["report_artifact_id"],
            "RPT-0000000001",
        )
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(
            payload["experiment"]["experiment_id"],
            "EXP-000001",
        )

    def test_atomic_write(self) -> None:
        report = self.build_report()

        with tempfile.TemporaryDirectory() as directory:
            paths = report.write_atomic(directory)

            self.assertTrue(paths["markdown"].exists())
            self.assertTrue(paths["manifest"].exists())

            self.assertFalse(
                Path(str(paths["markdown"]) + ".tmp").exists()
            )
            self.assertFalse(
                Path(str(paths["manifest"]) + ".tmp").exists()
            )

            payload = json.loads(
                paths["manifest"].read_text(encoding="utf-8")
            )

            self.assertEqual(
                payload["report_artifact_id"],
                "RPT-0000000001",
            )

    def test_sections_required(self) -> None:
        with self.assertRaises(ValueError):
            build_experiment_report(
                sequence=2,
                title="Invalid Report",
                authors=[],
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                sections=[],
                observation_ids=[],
                evaluation_result_ids=[],
                statistical_summary_ids=[],
            )


if __name__ == "__main__":
    unittest.main()
'@

Set-Content `
    -Path $ReportTestPath `
    -Value $ReportTests `
    -Encoding UTF8

# ------------------------------------------------------------
# 6. Version and Changelog
# ------------------------------------------------------------

Set-Content `
    -Path $VersionPath `
    -Value "0.6.0" `
    -Encoding UTF8

$NewChangelogSection = @'
## 0.6.0 - 2026-07-25

### Added

- Canonical Scientific Report Specification.
- Canonical scientific-report JSON Schema.
- Report-definition registry in CSV and JSON.
- Deterministic Markdown report generation.
- JSON report-manifest generation.
- Evidence-manifest hashing.
- Report-integrity hashing.
- Atomic report artifact writing.
- Experiment-level scientific report builder.
- Scientific report unit tests.

### Scientific policy

Reports communicate preserved evidence and do not replace underlying
observations, evaluations, or statistical summaries.

Results and interpretations remain explicitly separated.

Claims must remain proportional to evidence.

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

if ($ExistingBody -notmatch "(?m)^## 0\.6\.0 - 2026-07-25") {
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
Write-Host " PrimeAIExplorer v0.6"
Write-Host " Scientific Report Foundation"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

$RequiredFiles = @(
    $CanonicalReportPath,
    $ReportSchemaPath,
    $RegistryCsvPath,
    $RegistryJsonPath,
    $ReportModulePath,
    $ReportTestPath,
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
    "PrimeAIExplorer Canonical Scientific Report Specification",
    "REPORT-NNNNNN",
    "RPT-NNNNNNNNNN",
    "Claims must remain proportional to evidence.",
    "Results and Interpretation",
    "Negative and Null Results",
    "Reports communicate evidence.",
    "They do not replace evidence.",
    "Draw conclusions second."
)

$DocumentContent = Get-Content $CanonicalReportPath -Raw

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
    $Schema = Get-Content $ReportSchemaPath -Raw |
        ConvertFrom-Json

    if (
        $Schema.title -eq
        "PrimeAIExplorer Canonical Scientific Report"
    ) {
        Write-Host "[PASS] Scientific report schema JSON is valid"
    }
    else {
        Write-Host "[FAIL] Unexpected report schema title"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Scientific report schema JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

try {
    $RegistryJson = Get-Content $RegistryJsonPath -Raw |
        ConvertFrom-Json

    if ($RegistryJson.report_definitions.Count -eq 3) {
        Write-Host "[PASS] Report registry contains 3 definitions"
    }
    else {
        Write-Host "[FAIL] Unexpected report-definition count"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Report registry JSON is invalid"
    Write-Host $_.Exception.Message
    $Failed = $true
}

$CsvRows = @(
    Import-Csv $RegistryCsvPath
)

if ($CsvRows.Count -eq 3) {
    Write-Host "[PASS] Report registry CSV contains 3 definitions"
}
else {
    Write-Host "[FAIL] Unexpected report CSV count"
    $Failed = $true
}

$DuplicateIds = @(
    $CsvRows |
        Group-Object report_definition_id |
        Where-Object Count -gt 1
)

if ($DuplicateIds.Count -eq 0) {
    Write-Host "[PASS] No duplicate report-definition identifiers"
}
else {
    Write-Host "[FAIL] Duplicate report-definition identifiers"
    $Failed = $true
}

$InvalidIds = @(
    $CsvRows |
        Where-Object {
            $_.report_definition_id -notmatch "^REPORT-[0-9]{6}$"
        }
)

if ($InvalidIds.Count -eq 0) {
    Write-Host "[PASS] All report-definition identifiers are canonical"
}
else {
    Write-Host "[FAIL] Invalid report-definition identifiers"
    $Failed = $true
}

$Version = (Get-Content $VersionPath -Raw).Trim()

if ($Version -eq "0.6.0") {
    Write-Host "[PASS] VERSION is 0.6.0"
}
else {
    Write-Host "[FAIL] VERSION is not 0.6.0"
    $Failed = $true
}

Write-Host ""
Write-Host "Report registry:"

$CsvRows |
    Format-Table `
        report_definition_id,
        title,
        version,
        report_type,
        primary_experiment `
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
    Write-Host "Report tests:"

    py -m unittest `
        discover `
        -s tests `
        -p "test_report.py" `
        -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Report tests failed"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] Report tests passed"
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
Write-Host "Canonical report document line count:"

$LineCount = (Get-Content $CanonicalReportPath).Count
Write-Host $LineCount

if ($LineCount -lt 200) {
    Write-Host "[WARN] Canonical report document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "PRIMEAIEXPLORER v0.6 FAILED"
    exit 1
}

Write-Host ""
Write-Host "PRIMEAIEXPLORER v0.6 PASSED"