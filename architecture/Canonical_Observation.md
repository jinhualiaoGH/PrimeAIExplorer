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
