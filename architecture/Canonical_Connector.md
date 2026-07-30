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
