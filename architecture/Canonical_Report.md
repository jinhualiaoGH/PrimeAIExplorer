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

### REPORT-000001 â€” Experiment Scientific Report

Produces a complete experiment-level scientific report.

### REPORT-000002 â€” Run Validation Report

Reports execution, integrity, failure, and evidence-preservation status.

### REPORT-000003 â€” Condition Comparison Report

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
