# ============================================================
# PrimeAIExplorer v0.2
# Step 2 - Canonical Experiment Specification
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"
$ArchitectureDir = Join-Path $Root "architecture"
$ExperimentsDir  = Join-Path $Root "experiments"

New-Item -ItemType Directory -Path $ArchitectureDir -Force | Out-Null
New-Item -ItemType Directory -Path $ExperimentsDir -Force | Out-Null

$CanonicalExperiment = @"
# PrimeAIExplorer Canonical Experiment Specification

Version: 0.2.0  
Status: Foundation  
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of a scientific experiment
within PrimeAIExplorer.

Every experiment shall follow a common structure so that it can be understood,
validated, executed, compared, reproduced, extended, and independently reviewed.

The experiment is the primary scientific object.

AI models are experimental subjects.

---

## 2. Core Scientific Questions

Every experiment must state:

1. What is being studied?
2. Why is it being studied?
3. What hypothesis is being tested?
4. Which variables are controlled?
5. Which observations are collected?
6. How are the results evaluated?
7. How can the experiment be reproduced?

---

## 3. Canonical Identifier

Every experiment receives a permanent identifier:

EXP-NNNNNN

Examples:

- EXP-000001
- EXP-000002
- EXP-000125

The identifier shall never be reused.

Experiment revisions are represented through semantic versions.

---

## 4. Experiment Status

Permitted statuses are:

- Proposed
- Draft
- Review
- Approved
- Implemented
- Pilot
- Active
- Completed
- Suspended
- Retired
- Invalidated

Status changes must be recorded rather than silently overwritten.

---

## 5. Canonical Structure

Every experiment definition shall contain:

- Identity
- Scientific definition
- Variables
- Dataset
- Prompt
- Experimental subjects
- Execution protocol
- Observation policy
- Evaluation
- Statistical analysis
- Outputs
- Reproducibility
- Governance

---

## 6. Identity

Required identity fields:

- experiment_id
- title
- short_name
- version
- status
- created_date
- modified_date
- authors
- experimental_universe
- research_program

Example:

    experiment_id: EXP-000001
    title: Memory-Limited Learning
    short_name: memory_limited_learning
    version: 0.1.0
    status: Proposed
    experimental_universe: PrimeNet
    research_program: PrimeAIExplorer

---

## 7. Scientific Definition

Every experiment must define:

- research domain
- scientific question
- objective
- hypothesis
- null hypothesis
- motivation
- included scope
- excluded scope

Hypotheses must be declared before primary observations are interpreted.

Exploratory and confirmatory analyses must be distinguished.

---

## 8. Variables

Every experiment must document:

### Independent variables

Variables deliberately changed by the experiment.

### Dependent variables

Measurements expected to respond to changes in independent variables.

### Controlled variables

Conditions held constant across experimental groups.

### Nuisance variables

Known influences that cannot be fully controlled but must be recorded.

---

## 9. Dataset

Every experiment must reference a canonical, versioned dataset.

Required dataset properties include:

- permanent dataset identifier
- explicit version
- deterministic construction
- documented provenance
- immutable released artifacts
- cryptographic checksums
- explicit observation, validation, and test partitions

---

## 10. Prompt

Prompts are versioned scientific instruments.

Every execution must record:

- prompt identifier
- prompt version
- rendering parameters
- rendered prompt hash
- expected response schema
- model-specific adaptations, when necessary

Model-specific adaptations must not silently alter the scientific task.

---

## 11. Experimental Subjects

AI models are treated as scientific subjects.

Every model execution must record, when available:

- provider
- connector
- model identifier
- model version
- access method
- execution date
- decoding parameters
- context limits
- tool availability
- known provider-side changes

The experiment definition remains independent of any one model provider.

---

## 12. Execution Protocol

Every execution must specify:

- execution mode
- repetitions per condition
- randomization policy
- random seed, when applicable
- timeout
- retry policy
- failure policy
- cache policy

Dry-run mode must perform no paid model calls.

Failures and retries must be preserved as observations.

---

## 13. Observation Records

Every response becomes a permanent scientific observation.

Canonical observation identifiers use:

OBS-NNNNNNNNNN

Every observation must link to:

- experiment ID and version
- run ID
- condition ID
- model subject
- dataset ID and version
- prompt ID and version
- prompt hash
- raw response
- timestamp
- execution status
- cache status

Raw responses must never be silently modified.

Parsing and normalization produce derived artifacts linked to the raw response.

---

## 14. Evaluation

Evaluation methods must be defined before primary results are interpreted.

Objective metrics are preferred.

Every evaluation must record:

- evaluator identifier
- evaluator version
- primary metric
- secondary metrics
- invalid-response policy
- missing-output policy
- subjective rubric, when used
- human-review requirements, when used

---

## 15. Statistical Analysis

Every statistical plan must specify:

- sample size
- descriptive statistics
- confidence intervals, when applicable
- missing-data policy
- outlier policy
- inferential methods, when applicable
- multiple-comparison policy, when applicable

Observations must not be removed without documented justification.

---

## 16. Required Outputs

A completed run should produce:

- experiment_manifest.json
- run_manifest.json
- observations.jsonl
- evaluation_results.csv
- statistical_summary.json
- scientific_report.md

Generated artifacts must identify their source experiment, software version,
creation time, and originating observations.

---

## 17. Reproducibility

A reproducibility record should capture:

- operating system
- Python version
- dependency versions
- PrimeAIExplorer version
- source-control commit
- experiment version
- dataset version and checksum
- prompt version and hash
- connector version
- model identifier
- execution parameters
- evaluation version
- statistics version
- timestamps

---

## 18. Governance

Once an experiment enters Active status, its specification shall not be silently
edited.

Changes require:

1. A new version.
2. A documented amendment.
3. A description of scientific impact.
4. Preservation of the earlier version.

---

## 19. Scientific Safeguards

PrimeAIExplorer experiments shall not:

- change hypotheses after observing results without disclosure
- discard unsuccessful responses silently
- report only favorable repetitions
- compare materially different tasks as though they were identical
- infer internal model mechanisms solely from external behavior
- replace raw evidence with summaries
- claim universal behavior from limited observations

---

## 20. Guiding Statement

The canonical experiment specification exists to provide scientific clarity.

A well-defined experiment allows observations to be interpreted correctly,
reproduced independently, and compared fairly across models and time.

Make observations first.

Draw conclusions second.
"@

$RegistryCsv = @"
experiment_id,title,short_name,version,status,experimental_universe,created_date,modified_date
EXP-000001,Memory-Limited Learning,memory_limited_learning,0.1.0,Proposed,PrimeNet,2026-07-25,2026-07-25
EXP-000002,Compression Efficiency,compression_efficiency,0.1.0,Proposed,PrimeNet,2026-07-25,2026-07-25
EXP-000003,Emergence of Abstraction,emergence_of_abstraction,0.1.0,Proposed,PrimeNet,2026-07-25,2026-07-25
"@

$RegistryObject = [ordered]@{
    registry_name    = "PrimeAIExplorer Experiment Registry"
    registry_version = "0.2.0"
    updated_date     = "2026-07-25"
    experiments      = @(
        [ordered]@{
            experiment_id        = "EXP-000001"
            title                = "Memory-Limited Learning"
            short_name           = "memory_limited_learning"
            version              = "0.1.0"
            status               = "Proposed"
            experimental_universe = "PrimeNet"
            created_date         = "2026-07-25"
            modified_date        = "2026-07-25"
        },
        [ordered]@{
            experiment_id        = "EXP-000002"
            title                = "Compression Efficiency"
            short_name           = "compression_efficiency"
            version              = "0.1.0"
            status               = "Proposed"
            experimental_universe = "PrimeNet"
            created_date         = "2026-07-25"
            modified_date        = "2026-07-25"
        },
        [ordered]@{
            experiment_id        = "EXP-000003"
            title                = "Emergence of Abstraction"
            short_name           = "emergence_of_abstraction"
            version              = "0.1.0"
            status               = "Proposed"
            experimental_universe = "PrimeNet"
            created_date         = "2026-07-25"
            modified_date        = "2026-07-25"
        }
    )
}

$CanonicalPath = Join-Path $ArchitectureDir "Canonical_Experiment.md"
$RegistryCsvPath = Join-Path $ExperimentsDir "experiment_registry.csv"
$RegistryJsonPath = Join-Path $ExperimentsDir "experiment_registry.json"

Set-Content -Path $CanonicalPath -Value $CanonicalExperiment -Encoding UTF8
Set-Content -Path $RegistryCsvPath -Value $RegistryCsv -Encoding UTF8

$RegistryObject |
    ConvertTo-Json -Depth 10 |
    Set-Content -Path $RegistryJsonPath -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.2 - Step 2"
Write-Host " Canonical Experiment Specification"
Write-Host "============================================================"
Write-Host ""

$RequiredFiles = @(
    $CanonicalPath,
    $RegistryCsvPath,
    $RegistryJsonPath
)

$Failed = $false

foreach ($File in $RequiredFiles) {
    if (Test-Path $File) {
        $Item = Get-Item $File

        if ($Item.Length -gt 0) {
            Write-Host "[PASS] $($Item.FullName)"
            Write-Host "       Size: $($Item.Length) bytes"
        }
        else {
            Write-Host "[FAIL] Empty file: $File"
            $Failed = $true
        }
    }
    else {
        Write-Host "[FAIL] Missing file: $File"
        $Failed = $true
    }
}

try {
    $Json = Get-Content $RegistryJsonPath -Raw | ConvertFrom-Json

    if ($Json.experiments.Count -eq 3) {
        Write-Host "[PASS] Registry JSON contains 3 experiments"
    }
    else {
        Write-Host "[FAIL] Unexpected experiment count"
        $Failed = $true
    }
}
catch {
    Write-Host "[FAIL] Registry JSON validation failed"
    Write-Host $_.Exception.Message
    $Failed = $true
}

Write-Host ""
Import-Csv $RegistryCsvPath | Format-Table -AutoSize

if ($Failed) {
    Write-Host ""
    Write-Host "STEP 2 FAILED"
    exit 1
}

Write-Host ""
Write-Host "STEP 2 PASSED"