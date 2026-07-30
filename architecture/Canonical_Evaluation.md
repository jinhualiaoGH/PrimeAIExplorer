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

### METRIC-000001 â€” Exact Match Accuracy

Measures whether normalized predicted text exactly equals normalized expected
text.

Output:

- 1.0 for a match
- 0.0 for a non-match

Normalization must be explicitly configured and versioned.

### METRIC-000002 â€” Numeric Absolute Error

Measures the absolute difference between a predicted numeric value and expected
numeric value.

Formula:

absolute_error = absolute_value(prediction - expected)

Lower values are better.

### METRIC-000003 â€” Numeric Relative Error

Measures numeric error relative to the magnitude of the expected value.

The zero-target policy must be documented.

### METRIC-000004 â€” Response Validity

Measures whether the response satisfies the expected response contract.

Output:

- 1.0 for valid
- 0.0 for invalid

### METRIC-000005 â€” Abstention Indicator

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
