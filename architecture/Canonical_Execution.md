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
