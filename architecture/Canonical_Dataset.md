# PrimeAIExplorer Canonical Dataset Specification

Version: 0.2.0
Status: Foundation
Date: 2026-07-25

---

## 1. Purpose

This document defines the canonical representation of a scientific dataset
within PrimeAIExplorer.

A dataset is a versioned scientific object that supplies observations, tasks,
ground truth, and experimental conditions to one or more experiments.

Every dataset shall be constructed, validated, registered, preserved, and
referenced through a permanent dataset identifier.

Datasets must not exist only as unnamed files or temporary prompt content.

---

## 2. Core Principle

A PrimeAIExplorer dataset must answer the following questions:

1. What scientific observations does the dataset contain?
2. Where did those observations originate?
3. How was the dataset constructed?
4. Which transformations were applied?
5. How is ground truth defined?
6. How is the dataset partitioned?
7. How is leakage prevented?
8. How is integrity verified?
9. How can the dataset be reproduced?
10. Which experiments use the dataset?

---

## 3. Canonical Dataset Identifier

Every dataset receives a permanent identifier using this format:

DS-NNNNNN

Examples:

- DS-000001
- DS-000002
- DS-000125

Rules:

- A dataset identifier is permanent.
- A dataset identifier shall never be reused.
- A released dataset version shall never be silently modified.
- Dataset revisions are represented through semantic versions.
- Retired and invalidated datasets remain preserved in the registry.
- Derived datasets receive their own permanent identifiers.

---

## 4. Dataset Versioning

Dataset versions shall use semantic versioning:

MAJOR.MINOR.PATCH

Examples:

- 0.1.0
- 1.0.0
- 1.1.0
- 2.0.0

Recommended interpretation:

### MAJOR

Used when a dataset changes in a scientifically incompatible way.

Examples:

- different source universe
- changed ground-truth definition
- changed partition policy
- changed sampling design
- removal or replacement of observations

### MINOR

Used when compatible scientific content is added.

Examples:

- additional partitions
- new metadata
- expanded scale
- additional validated observations

### PATCH

Used for corrections that do not materially alter the scientific meaning.

Examples:

- metadata correction
- documentation correction
- checksum manifest repair
- non-scientific formatting correction

Every released version shall remain independently identifiable.

---

## 5. Canonical Dataset Status

Permitted statuses are:

- Proposed
- Draft
- Building
- Validation
- Released
- Active
- Suspended
- Retired
- Invalidated

Status definitions:

### Proposed

The dataset has been conceptually defined but not yet constructed.

### Draft

The specification is being developed.

### Building

Construction is in progress.

### Validation

Construction is complete and integrity checks are running.

### Released

The dataset is immutable and approved for scientific use.

### Active

The released dataset is currently used by one or more experiments.

### Suspended

Use is temporarily paused pending review.

### Retired

The dataset is preserved but no longer recommended for new experiments.

### Invalidated

A scientific or technical defect makes the dataset unsuitable for use.

---

## 6. Canonical Dataset Structure

Every dataset definition shall contain:

- Identity
- Scientific purpose
- Source universe
- Provenance
- Construction
- Representation
- Ground truth
- Partitioning
- Leakage controls
- Validation
- Integrity
- Licensing and access
- Experiment relationships
- Reproducibility
- Governance

---

## 7. Dataset Identity

Required identity fields include:

- dataset_id
- title
- short_name
- version
- status
- created_date
- modified_date
- released_date
- authors
- source_universe
- dataset_family
- research_program

Example:

    dataset_id: DS-000001
    title: Prime Gap Memory-Limited Learning Dataset
    short_name: prime_gap_memory_limited_learning
    version: 0.1.0
    status: Proposed
    source_universe: PrimeNet
    dataset_family: prime_gap_sequences
    research_program: PrimeAIExplorer

The short name shall use lowercase snake_case.

---

## 8. Scientific Purpose

Every dataset must state:

- scientific objective
- intended experiments
- intended tasks
- target capabilities
- included scope
- excluded scope
- known limitations

A dataset shall not be described only by its file format or size.

Its scientific role must be explicit.

Example target capabilities include:

- memory
- compression
- pattern discovery
- abstraction
- generalization
- reasoning
- scientific hypothesis generation

---

## 9. Source Universe

Every dataset must identify the experimental universe from which it originates.

PrimeNet is the first experimental universe supported by PrimeAIExplorer.

A source universe may provide:

- canonical observations
- deterministic construction
- exact mathematical ground truth
- large-scale repositories
- validated manifests
- reproducible coordinate systems

The source universe reference should identify:

- source system
- source version
- source path or logical identifier
- source manifest
- source checksum
- extraction range
- extraction date
- extraction software version

---

## 10. Provenance

Dataset provenance describes the complete path from source observations to
released dataset artifacts.

Required provenance information includes:

- original source
- source identifier
- extraction method
- transformation sequence
- filtering rules
- sampling rules
- partition assignment
- ground-truth generation
- validation procedures
- software version
- source-control commit
- execution timestamp

Every derived artifact shall remain traceable to its source observations.

Provenance must be machine-readable where practical.

---

## 11. Dataset Construction

Dataset construction must be deterministic whenever practical.

A construction specification should define:

- input sources
- coordinate ranges
- record selection rules
- exclusion rules
- ordering rules
- transformation rules
- random seed
- sampling algorithm
- partitioning algorithm
- output schema
- output formats

When randomness is used:

- the algorithm must be documented
- the seed must be recorded
- the resulting selected identifiers must be preserved
- reruns must be able to reproduce the same release

---

## 12. Canonical Ordering

Dataset ordering shall be explicitly defined.

Examples include:

- prime index order
- numeric coordinate order
- chronological order
- deterministic shuffled order
- grouped experimental-condition order

File-system lexical ordering must not be assumed to represent scientific order.

For PrimeNet-derived datasets, canonical prime-index or numeric-coordinate order
should be used unless the dataset specification states otherwise.

---

## 13. Dataset Representation

Every dataset shall define its record schema.

A record schema should document:

- field name
- data type
- required status
- nullable status
- unit
- valid range
- scientific meaning
- source
- transformation

Recommended machine-readable formats include:

- JSON Lines
- CSV
- Parquet
- NumPy
- JSON manifests

Human-readable documentation may use Markdown.

Binary formats must have a documented schema and reader implementation.

---

## 14. Canonical Record Identity

Every dataset record should have a stable identifier when practical.

Recommended format:

REC-DSNNNNNN-NNNNNNNNNN

Example:

REC-DS000001-0000000001

A record identifier should remain stable within a released dataset version.

The record identifier should allow linkage among:

- source observation
- rendered prompt
- model response
- evaluation result
- statistical analysis

---

## 15. Ground Truth

Every task requiring correctness evaluation must define ground truth.

Ground truth may be:

- directly observed
- mathematically computed
- deterministically derived
- independently validated
- externally referenced

The ground-truth specification must document:

- definition
- generating algorithm
- numeric precision
- tolerance
- validation method
- known uncertainty
- missing-value policy

Ground truth shall not be inferred from model consensus.

For deterministic mathematical universes, exact ground truth is preferred.

---

## 16. Dataset Partitions

Datasets should use explicit scientific partitions.

Recommended partition roles include:

- observation
- calibration
- validation
- hidden_evaluation
- stress_test
- out_of_distribution
- challenge

### Observation partition

Information shown to the model as context or examples.

### Calibration partition

Used to validate prompts, parsers, and evaluation procedures.

### Validation partition

Used during experiment development without exposing final hidden evaluation
content.

### Hidden-evaluation partition

Reserved for final scientific measurement.

### Stress-test partition

Contains difficult, extreme, or adversarially selected conditions.

### Out-of-distribution partition

Tests generalization beyond the observational regime.

Partition names and roles must be documented.

---

## 17. Partition Independence

Dataset partitions must be scientifically independent according to the task.

Potential overlap must be checked across:

- exact records
- source coordinates
- windows
- repeated sequences
- transformed duplicates
- near-duplicates
- target labels
- prompt examples

Partition boundaries must reflect the intended generalization question.

For sequence and window datasets, overlapping source windows must be handled
carefully because shared observations can create hidden leakage.

---

## 18. Leakage Prevention

PrimeAIExplorer shall treat data leakage as a scientific integrity issue.

Leakage controls should check:

- duplicate records
- overlapping source coordinates
- overlapping windows
- repeated target values
- prompt examples appearing in evaluation
- normalization using hidden-test statistics
- partition assignment after observing outcomes
- cached model responses from prior exposure

Every dataset should contain a leakage-audit report.

Any known leakage must be disclosed.

A dataset with material undisclosed leakage shall not be released.

---

## 19. Memory-Limited Dataset Design

Datasets for memory-limited learning experiments must vary available observation
content without unintentionally changing the task.

A memory condition may vary:

- observation count
- token count
- sequence length
- compressed representation size
- summary depth
- retrieval budget

The target evaluation set should remain fixed across memory conditions unless
the experiment explicitly studies another variable.

Recommended memory conditions for initial pilot work include:

- 10 observations
- 25 observations
- 50 observations
- 100 observations
- 250 observations
- 500 observations

The final condition design must be validated against model context limits.

---

## 20. PrimeNet-Derived Dataset Requirements

A PrimeNet-derived dataset should record:

- PrimeNet repository version
- prime or gap repository identifier
- source partition files
- source coordinate range
- prime-index range
- numeric-value range
- source data type
- boundary ownership policy
- source manifest
- source checksum
- extraction software
- extraction parameters

For gap datasets, the ownership convention must be explicit.

PrimeNet canonical gap data uses left-owned full mode:

One stored prime index owns one outgoing gap.

Boundary and terminal behavior must be preserved or explicitly transformed.

---

## 21. Dataset Validation

Every released dataset must pass validation.

Recommended validation categories include:

### Schema validation

- required fields present
- valid data types
- valid values
- no unexpected columns

### Count validation

- expected record counts
- partition counts
- class counts
- condition counts

### Range validation

- valid numeric ranges
- valid coordinate ranges
- valid prime indexes
- valid gap values

### Ordering validation

- canonical ordering
- no accidental lexical ordering
- no unexpected duplicates

### Ground-truth validation

- recomputation of selected records
- independent validation samples
- tolerance checks

### Partition validation

- no unauthorized overlap
- deterministic partition assignment
- expected proportions

### Integrity validation

- artifact checksums
- manifest checksums
- file sizes
- successful readback

Validation outputs shall be preserved.

---

## 22. Checksums and Integrity

Every released artifact shall have a cryptographic checksum.

SHA-256 is the default checksum algorithm.

A dataset release should include:

- artifact filename
- artifact size
- SHA-256 checksum
- record count
- schema version
- creation timestamp

Checksums protect against accidental modification and enable independent
verification.

A checksum change creates a new artifact and may require a new dataset version.

---

## 23. Canonical Dataset Manifest

Each dataset release should include a machine-readable manifest.

Recommended manifest fields include:

- dataset_id
- dataset_version
- title
- status
- source_universe
- source_version
- schema_version
- partition definitions
- artifact inventory
- record counts
- checksums
- construction software version
- source-control commit
- creation timestamp
- validation status
- known limitations

The manifest is the canonical index of the released dataset.

---

## 24. Dataset Directory Layout

Recommended dataset specification layout:

    datasets/
    |
    +-- dataset_registry.csv
    +-- dataset_registry.json
    |
    +-- DS-000001_prime_gap_memory_limited_learning/
        |
        +-- README.md
        +-- dataset.yaml
        +-- schema.json
        +-- construction.yaml
        +-- partitions.yaml
        +-- provenance.json
        +-- validation/
        +-- scripts/
        +-- tests/
        +-- releases/

Recommended release layout:

    releases/
    |
    +-- v0.1.0/
        |
        +-- manifest.json
        +-- checksums.sha256
        +-- observation.jsonl
        +-- calibration.jsonl
        +-- validation.jsonl
        +-- hidden_evaluation.jsonl
        +-- validation_report.json

Dataset specifications and generated release artifacts should remain separate.

---

## 25. Registry Requirements

Every canonical dataset must appear in:

- dataset_registry.csv
- dataset_registry.json

The registry should contain:

- dataset ID
- title
- short name
- version
- status
- source universe
- dataset family
- primary experiment
- created date
- modified date

The CSV registry supports easy inspection.

The JSON registry supports machine-readable integration.

The two registries must remain logically consistent.

---

## 26. Dataset and Experiment Relationship

A dataset may support multiple experiments.

An experiment may use multiple datasets.

Every relationship should declare the dataset role.

Recommended roles include:

- primary
- calibration
- baseline
- validation
- external_comparison
- stress_test

The experiment specification should reference a permanent dataset ID and
version rather than a mutable directory path alone.

---

## 27. Dataset Immutability

Released dataset artifacts are immutable.

A released file shall not be edited in place.

Corrections require:

1. A new dataset version.
2. A documented change record.
3. Regenerated checksums.
4. Revalidation.
5. Preservation of the earlier release.

Draft datasets may change before release, but draft changes should still be
tracked through source control.

---

## 28. Dataset Access and Licensing

Every dataset must document:

- access level
- distribution policy
- license
- third-party restrictions
- privacy considerations
- security considerations
- export or regulatory constraints, when applicable

PrimeNet mathematical observations are intended to support open,
reproducible scientific research, subject to the repository's final license.

No private or sensitive user information should be incorporated into canonical
experimental datasets.

---

## 29. Cost-Aware Dataset Design

Dataset design should support free development before paid model execution.

Before commercial API calls are used, datasets should support:

- schema validation
- dry-run rendering
- deterministic mock-model execution
- local baseline execution
- evaluation testing
- statistics testing
- report generation
- cache-key validation

Dataset defects should be discovered before paid observations are collected.

---

## 30. Scientific Safeguards

PrimeAIExplorer datasets shall not:

- conceal source provenance
- silently alter released records
- combine partitions without disclosure
- define ground truth using the tested model
- expose hidden-evaluation targets in prompts
- assign partitions after observing model performance
- omit failed construction records without documentation
- rely on undocumented manual corrections
- claim independence when source windows overlap materially
- replace exact mathematical ground truth with model consensus

---

## 31. First Canonical Dataset

The first proposed PrimeAIExplorer dataset is:

Dataset ID:

DS-000001

Title:

Prime Gap Memory-Limited Learning Dataset

Short name:

prime_gap_memory_limited_learning

Source universe:

PrimeNet

Primary experiment:

EXP-000001

Purpose:

Study how available observational context influences model prediction,
generalization, consistency, abstraction, and information efficiency over
deterministic prime-gap sequences.

Initial status:

Proposed

Initial version:

0.1.0

No scientific release has yet been created.

---

## 32. Future Dataset Families

Potential dataset families include:

- prime_gap_sequences
- selected_gap_events
- transition_matrices
- entropy_profiles
- cross_scale_windows
- prime_information_geometry
- symbolic_pattern_tasks
- compression_tasks
- abstraction_tasks
- scientific_reasoning_tasks

Each family must follow this canonical specification.

---

## 33. Reproducibility Commitment

A dataset is scientifically useful only when another researcher can determine:

- exactly what it contains
- exactly where it came from
- exactly how it was constructed
- exactly how its partitions were assigned
- exactly how ground truth was obtained
- exactly how integrity was validated

PrimeAIExplorer shall preserve this information as part of every released
dataset.

---

## 34. Guiding Statement

Datasets are not merely inputs to model calls.

They are scientific instruments.

Their design determines which questions can be answered and which conclusions
are justified.

Make observations first.

Draw conclusions second.

---

End of Document
