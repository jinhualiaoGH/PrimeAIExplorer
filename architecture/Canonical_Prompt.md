# PrimeAIExplorer Canonical Prompt Specification

Version: 0.2.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of prompts within
PrimeAIExplorer.

A prompt is a versioned scientific instrument.

It communicates an experimental task to an AI model and therefore directly
influences the observations produced by the experiment.

Prompts must not be treated as temporary text copied manually into a chat
window without provenance, versioning, or validation.

Every canonical prompt shall be registered, reproducible, reviewable, and
linked to the experiment and dataset it serves.

---

## 2. Core Principle

A PrimeAIExplorer prompt must answer the following questions:

1. Which experiment does the prompt serve?
2. Which dataset records does it render?
3. What task is presented to the model?
4. What information is visible to the model?
5. Which information is intentionally hidden?
6. What output format is required?
7. How are prompt variables rendered?
8. How is the rendered prompt identified?
9. How are model-specific adaptations controlled?
10. How can the exact prompt be reproduced?

---

## 3. Canonical Prompt Identifier

Every prompt receives a permanent identifier using this format:

PROMPT-NNNNNN

Examples:

- PROMPT-000001
- PROMPT-000002
- PROMPT-000125

Rules:

- A prompt identifier is permanent.
- A prompt identifier shall never be reused.
- Released prompt versions shall not be silently modified.
- Prompt revisions use semantic versions.
- Retired and invalidated prompts remain preserved.
- Substantially different scientific tasks receive different prompt IDs.

---

## 4. Prompt Versioning

Prompt versions shall use semantic versioning:

MAJOR.MINOR.PATCH

Examples:

- 0.1.0
- 1.0.0
- 1.1.0
- 2.0.0

Recommended interpretation:

### MAJOR

Used when the scientific task changes incompatibly.

Examples:

- changed question
- changed visible information
- changed target behavior
- changed response meaning
- changed scoring interpretation

### MINOR

Used when compatible functionality is added.

Examples:

- additional optional metadata
- improved formatting
- added supported conditions
- added compatible response fields

### PATCH

Used for scientifically neutral corrections.

Examples:

- spelling correction
- punctuation correction
- formatting repair
- documentation clarification

Any change that could influence model behavior should be treated conservatively
and documented.

---

## 5. Canonical Prompt Status

Permitted statuses are:

- Proposed
- Draft
- Review
- Approved
- Active
- Suspended
- Retired
- Invalidated

### Proposed

The prompt has been conceptually defined.

### Draft

The template is being developed.

### Review

Scientific and technical review is in progress.

### Approved

The prompt is approved for implementation.

### Active

The prompt is currently used in experiments.

### Suspended

Use is paused pending review.

### Retired

The prompt is preserved but not recommended for new experiments.

### Invalidated

The prompt contains a defect that compromises scientific use.

---

## 6. Canonical Prompt Structure

Every prompt specification shall contain:

- Identity
- Scientific role
- Message structure
- Template variables
- Dataset linkage
- Condition linkage
- Context policy
- Output contract
- Rendering rules
- Hashing rules
- Model adaptations
- Validation
- Leakage controls
- Reproducibility
- Governance

---

## 7. Prompt Identity

Required identity fields include:

- prompt_id
- title
- short_name
- version
- status
- created_date
- modified_date
- authors
- experiment_id
- dataset_id
- prompt_family
- research_program

Example:

    prompt_id: PROMPT-000001
    title: Memory-Limited Prime Gap Prediction Prompt
    short_name: memory_limited_prime_gap_prediction
    version: 0.1.0
    status: Proposed
    experiment_id: EXP-000001
    dataset_id: DS-000001
    prompt_family: memory_limited_learning
    research_program: PrimeAIExplorer

The short name shall use lowercase snake_case.

---

## 8. Scientific Role

Every prompt must state:

- scientific objective
- task definition
- target capability
- visible evidence
- hidden evidence
- expected model behavior
- prohibited assistance
- intended evaluation

Example target capabilities include:

- memory
- compression
- pattern discovery
- abstraction
- generalization
- reasoning
- scientific explanation

The prompt specification must describe the scientific task rather than only the
wording of the prompt.

---

## 9. Message Structure

PrimeAIExplorer distinguishes message roles explicitly.

Supported message roles may include:

- system
- developer
- user
- assistant_example
- tool
- metadata

The canonical prompt must document which roles are used.

A typical prompt may contain:

### System message

Defines stable task behavior and output constraints.

### User message

Contains dataset-derived observations and the current task.

### Assistant example

Provides a controlled demonstration when the experiment permits examples.

Examples must not reveal hidden evaluation targets.

Message ordering must be deterministic.

---

## 10. System and User Separation

System instructions and user content shall be stored separately.

The system message should define:

- experiment role
- permitted reasoning behavior
- output constraints
- refusal policy
- uncertainty policy
- formatting requirements

The user message should define:

- visible observations
- condition-specific information
- task question
- required response fields

Separating these components improves reproducibility and provider portability.

---

## 11. Template Variables

Prompt templates may contain explicit variables.

Recommended syntax:

    {{variable_name}}

Examples:

    {{observation_count}}
    {{prime_gap_sequence}}
    {{target_position}}
    {{response_schema}}
    {{experiment_condition}}
    {{dataset_record_id}}

Every variable must define:

- name
- type
- source
- required status
- permitted values
- escaping policy
- rendering policy
- missing-value policy

Undocumented variables are not permitted in released prompts.

---

## 12. Deterministic Rendering

Prompt rendering shall be deterministic whenever practical.

Identical inputs should produce identical rendered prompts.

Rendering must define:

- variable ordering
- whitespace normalization
- line endings
- numeric formatting
- list formatting
- separator rules
- Unicode normalization
- missing-value handling
- escaping behavior

Dynamic timestamps should not be inserted unless scientifically required.

Provider-generated wrappers must not be confused with the canonical prompt.

---

## 13. Dataset Linkage

Every rendered prompt shall link to canonical dataset records.

Required linkage may include:

- dataset ID
- dataset version
- partition
- record ID
- source coordinate
- observation window
- target record
- condition ID

The rendered prompt must not rely only on a mutable filename.

Prompt provenance should allow reconstruction of the exact visible observations.

---

## 14. Condition Linkage

Every rendered prompt shall identify its experimental condition.

Examples include:

- memory budget
- observation count
- compression level
- context representation
- summary depth
- task difficulty
- out-of-distribution status

Condition identifiers should use a stable format such as:

COND-EXP000001-001

The condition must be linked to the experiment specification.

---

## 15. Context Budget

Context is an independent scientific variable in many PrimeAIExplorer
experiments.

Every rendered prompt should record:

- observation count
- character count
- byte count
- approximate token count
- provider-specific token count when available
- message count
- maximum permitted context
- reserved output budget

Token counts must identify the tokenizer or estimation method.

Character count must not be silently treated as token count.

---

## 16. Memory-Limited Prompt Design

Memory-limited experiments must change the amount of available information
without unintentionally changing the task.

Potential memory conditions include:

- 10 observations
- 25 observations
- 50 observations
- 100 observations
- 250 observations
- 500 observations

Across memory conditions, the following should remain constant unless otherwise
documented:

- scientific question
- target record
- output schema
- evaluation procedure
- model parameters
- instruction wording
- visible metadata
- dataset version

The target evaluation case should remain fixed across memory conditions when
isolating the effect of memory.

---

## 17. Canonical Output Contract

Every prompt shall define the expected response structure.

The output contract may be:

- plain text
- integer
- decimal
- categorical label
- JSON object
- JSON array
- structured explanation

Structured output is preferred when objective evaluation is possible.

Example conceptual response fields:

    prediction
    confidence
    explanation
    abstain
    detected_pattern

The output contract must define:

- required fields
- optional fields
- data types
- valid ranges
- allowed labels
- null policy
- invalid-response policy

---

## 18. Response Schema Identifier

Every reusable response schema should receive an identifier.

Recommended format:

RESPONSE-NNNNNN

Example:

RESPONSE-000001

The response schema version must be recorded separately from the prompt version
when the schema is independently reusable.

A prompt may reference:

- response schema ID
- response schema version
- schema file
- parser version
- validation policy

---

## 19. Prompt Hashing

Every rendered prompt shall have a cryptographic hash.

SHA-256 is the default algorithm.

The canonical hash input should include:

- ordered message roles
- rendered message content
- template version
- rendering version
- relevant output schema reference

Prompt metadata not visible to the model should be hashed separately when
needed.

The prompt hash enables:

- reproducibility
- caching
- duplicate detection
- observation linkage
- integrity verification

---

## 20. Canonical Hash Representation

Before hashing, prompt content should use a canonical representation.

Recommended rules include:

- UTF-8 encoding
- LF line endings
- Unicode normalization form NFC
- deterministic message ordering
- no trailing whitespace
- deterministic separators
- explicit role labels

Example conceptual representation:

    SYSTEM
    <system content>

    USER
    <user content>

The exact canonicalization algorithm shall be versioned.

---

## 21. Model-Specific Adaptations

Different providers may require different message formats.

PrimeAIExplorer may adapt transport formatting while preserving the scientific
task.

Permitted adaptations may include:

- mapping canonical roles to provider roles
- wrapping JSON schema instructions
- converting unsupported message roles
- applying provider-required escaping
- inserting documented transport metadata

Model-specific adaptations shall not silently:

- add hints
- remove constraints
- reveal hidden targets
- change examples
- alter the scientific question
- change the output meaning

Every adaptation must be versioned and recorded.

---

## 22. Prompt Equivalence

Two rendered prompts are scientifically equivalent only when any differences
are not expected to materially influence the task.

Exact textual identity is stronger than claimed equivalence.

When prompts differ across providers, PrimeAIExplorer should record:

- canonical prompt hash
- provider-rendered prompt hash
- adaptation version
- adaptation description
- equivalence justification

Cross-model comparisons must disclose material prompt differences.

---

## 23. Prompt Leakage Prevention

Prompt leakage is a scientific integrity concern.

The prompt must not expose:

- hidden-evaluation targets
- future sequence values
- answer keys
- evaluator rules that reveal the answer
- labels from hidden partitions
- cached model answers
- identifying hints that encode the target

Examples and demonstrations must be checked for overlap with evaluation records.

Prompt rendering shall preserve dataset partition boundaries.

---

## 24. Prompt Injection and Untrusted Data

Dataset-derived text may contain instructions or adversarial content in some
experimental universes.

Such content must be treated as data rather than trusted instructions unless
the experiment explicitly studies instruction following.

The prompt specification should define:

- trusted instruction channels
- untrusted data channels
- escaping policy
- delimiter policy
- injection detection
- failure behavior

PrimeNet mathematical data is deterministic and low risk, but the architecture
shall support broader experimental universes safely.

---

## 25. Prompt Validation

Every released prompt must pass validation.

Recommended checks include:

### Identity validation

- canonical prompt ID
- semantic version
- registered experiment
- registered dataset

### Template validation

- all variables declared
- no undeclared variables
- no unresolved placeholders
- deterministic rendering
- valid encoding

### Output validation

- response schema exists
- parser can read valid examples
- invalid examples are rejected
- required fields are enforced

### Context validation

- observation count correct
- character count recorded
- token estimate recorded
- prompt fits configured context limit

### Leakage validation

- hidden targets absent
- evaluation records absent from examples
- partition boundaries preserved

### Integrity validation

- template hash
- rendered prompt hash
- successful readback
- registry consistency

Validation reports shall be preserved.

---

## 26. Prompt Registry

Every canonical prompt must appear in:

- prompt_registry.csv
- prompt_registry.json

The registry should contain:

- prompt ID
- title
- short name
- version
- status
- prompt family
- experiment ID
- dataset ID
- response schema ID
- created date
- modified date

The CSV registry supports inspection.

The JSON registry supports machine-readable integration.

The two registries must remain logically consistent.

---

## 27. Prompt Directory Layout

Recommended layout:

    prompts/
    |
    +-- prompt_registry.csv
    +-- prompt_registry.json
    |
    +-- PROMPT-000001_memory_limited_prime_gap_prediction/
        |
        +-- README.md
        +-- prompt.yaml
        +-- system.txt
        +-- user_template.txt
        +-- variables.json
        +-- response_schema.json
        +-- examples/
        +-- validation/
        +-- tests/
        +-- releases/

Recommended release layout:

    releases/
    |
    +-- v0.1.0/
        |
        +-- manifest.json
        +-- system.txt
        +-- user_template.txt
        +-- variables.json
        +-- response_schema.json
        +-- checksums.sha256

Prompt specifications and generated prompts should remain separate.

---

## 28. Prompt Immutability

Released prompt artifacts are immutable.

A released prompt file shall not be edited in place.

Changes require:

1. A new prompt version.
2. A documented change record.
3. New hashes.
4. Revalidation.
5. Preservation of the earlier release.

Draft prompts may change before release, but changes should remain under source
control.

---

## 29. Prompt and Observation Relationship

Every observation must reference:

- prompt ID
- prompt version
- rendered prompt hash
- provider-rendered prompt hash when applicable
- rendering engine version
- response schema ID
- response schema version

Raw prompt content should be preserved with the observation or be reproducible
from immutable artifacts and recorded variables.

---

## 30. Prompt and Cache Relationship

Prompt hashes are essential cache inputs.

A cache key may include:

- experiment version
- dataset checksum
- record ID
- condition ID
- prompt ID
- prompt version
- rendered prompt hash
- provider adaptation version
- model identifier
- model parameters

A cached response must remain linked to the original observation.

Cache reuse must be explicit rather than hidden.

---

## 31. Dry-Run Support

Every canonical prompt should support dry-run rendering.

Dry-run mode should:

- load the prompt specification
- load dataset records
- render messages
- validate variables
- calculate hashes
- estimate context usage
- validate response schemas
- write manifests
- perform no paid model calls

Dry-run success is required before commercial API execution.

---

## 32. Deterministic Baseline Support

Prompts should be executable against deterministic test subjects where
practical.

Examples include:

- echo connector
- fixed-response connector
- rule-based baseline
- known-answer mock model
- schema-validation model

These baselines validate the execution and evaluation pipeline without cost.

---

## 33. First Canonical Prompt

The first proposed PrimeAIExplorer prompt is:

Prompt ID:

PROMPT-000001

Title:

Memory-Limited Prime Gap Prediction Prompt

Short name:

memory_limited_prime_gap_prediction

Prompt family:

memory_limited_learning

Primary experiment:

EXP-000001

Primary dataset:

DS-000001

Response schema:

RESPONSE-000001

Purpose:

Present controlled quantities of prime-gap observations and ask the model to
produce a structured prediction for a hidden continuation task.

Initial status:

Proposed

Initial version:

0.1.0

No scientific release has yet been created.

---

## 34. Additional Proposed Prompts

PROMPT-000002

Title:

Prime Gap Compression Prompt

Primary experiment:

EXP-000002

Primary dataset:

DS-000002

Purpose:

Evaluate how effectively a model compresses deterministic prime-gap
observations while preserving information relevant to later tasks.

PROMPT-000003

Title:

Prime Structure Abstraction Prompt

Primary experiment:

EXP-000003

Primary dataset:

DS-000003

Purpose:

Evaluate whether a model can derive reusable abstractions from deterministic
prime-structure observations.

---

## 35. Scientific Safeguards

PrimeAIExplorer prompts shall not:

- reveal hidden evaluation targets
- silently change between repetitions
- mix provider-specific hints into one model only
- leave unresolved variables
- use undocumented examples
- omit system instructions from provenance
- change output requirements after observing results
- treat token estimates as exact counts without disclosure
- compare materially different prompts as identical
- overwrite released prompt versions
- discard rendered prompt hashes
- expose evaluation answers through formatting cues

---

## 36. Reproducibility Commitment

A prompt is scientifically useful only when another researcher can determine:

- exactly which instructions were used
- exactly which observations were visible
- exactly which variables were rendered
- exactly which output was requested
- exactly how the prompt was canonicalized
- exactly how the prompt was hashed
- exactly which provider adaptation was used

PrimeAIExplorer shall preserve this information for every observation.

---

## 37. Guiding Statement

Prompts are not merely text sent to models.

They are scientific instruments.

Their wording, structure, visible evidence, and output contracts influence the
behavior being measured.

Make observations first.

Draw conclusions second.

---

End of Document
