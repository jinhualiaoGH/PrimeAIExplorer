# PrimeAIExplorer Architecture Specification v1.0

## 1. Purpose

PrimeAIExplorer is a scientific benchmarking platform for evaluating how AI
models recognize, infer, and continue mathematical structures from finite
observations.

Prime-number-derived sequences are the reference scientific domain, but the
platform architecture is sequence-agnostic.

## 2. Architectural principles

1. Preserve scientific reproducibility.
2. Separate mathematical sequence generation from model execution.
3. Separate model execution from evaluation.
4. Add new capabilities through plugins.
5. Keep generated artifacts separate from source code.
6. Avoid hidden mutation of source datasets.
7. Record every experiment configuration and execution environment.
8. Keep public experiment inputs separate from private answer keys.
9. Maintain backward compatibility where practical.
10. Require tests for every stable public contract.

## 3. System layers

```text
PrimeNet Repository
        ↓
Repository Adapter
        ↓
Sequence Engine
        ↓
Experiment Engine
        ↓
Prompt Engine
        ↓
Connector Engine
        ↓
Execution Engine
        ↓
Evaluation Engine
        ↓
Reporting Engine
        ↓
Publication Engine
```

## 4. Layer responsibilities

### 4.1 Repository Adapter

Responsibilities:

- Read canonical PrimeNet partitions.
- Validate partition order and adjacency.
- Provide read-only access.
- Expose repository provenance.
- Never modify PrimeNet source files.

### 4.2 Sequence Engine

Responsibilities:

- Build derived mathematical sequences.
- Validate mathematical definitions.
- Generate sequence windows.
- Expose targets and metadata.
- Supply structural-validity rules.

Examples:

- prime gaps,
- left twin primes,
- right twin primes,
- twin-prime gaps,
- prime constellations.

### 4.3 Experiment Engine

Responsibilities:

- Interpret declarative experiment configurations.
- Generate cases.
- Assign stable case identifiers.
- Separate public cases from answer keys.
- Record sampling parameters.

### 4.4 Prompt Engine

Responsibilities:

- Render prompts from public cases.
- Preserve prompt templates.
- Hash exact prompts.
- Support hidden and disclosed definitions.
- Enforce response contracts.

### 4.5 Connector Engine

Responsibilities:

- Provide a common model interface.
- Register model connectors.
- Validate connector capabilities.
- Execute requests.
- Record latency, usage, and errors.
- Never expose API secrets in run artifacts.

### 4.6 Execution Engine

Responsibilities:

- Run cases through connectors.
- Support retries and checkpoints.
- Preserve deterministic ordering.
- Record execution state.
- Prevent duplicate case execution unless requested.

### 4.7 Evaluation Engine

Responsibilities:

- Parse responses.
- Compute common metrics.
- Apply sequence-specific validity checks.
- Measure confidence calibration.
- Export machine-readable results.

### 4.8 Reporting Engine

Responsibilities:

- Summarize results.
- Produce CSV, JSON, and Markdown reports.
- Generate model and representation comparisons.
- Preserve references to evidence files.

### 4.9 Publication Engine

Responsibilities:

- Generate publication-ready figures and tables.
- Produce manuscript-support artifacts.
- Never alter raw run evidence.

## 5. Canonical project layout

```text
PrimeAIExplorer/
├── core/
├── connectors/
├── plugins/
│   ├── sequences/
│   ├── evaluators/
│   └── reports/
├── experiments/
├── runs/
├── reports/
├── publication/
├── schemas/
├── templates/
├── scripts/
├── tests/
├── docs/
├── run_experiment.py
├── pyproject.toml
└── README.md
```

## 6. Data flow

```text
Repository data
    ↓
Validated sequence dataset
    ↓
Public case + private answer key
    ↓
Prompt
    ↓
Model response
    ↓
Parsed response
    ↓
Metric records
    ↓
Summary report
```

## 7. Artifact separation

Source-controlled:

```text
core/
connectors/
plugins/
schemas/
templates/
scripts/
tests/
docs/
experiment configurations
```

Generated:

```text
datasets/
cases/
prompts/
responses/
runs/
results/
reports/
publication output
```

Generated artifacts must not be imported as source modules.

## 8. Stability policy

The following become stable public contracts at v1.0:

- sequence plugin interface,
- connector interface,
- experiment schema,
- response schema,
- run manifest schema,
- evaluation record schema,
- directory conventions.

Internal implementation may change when these contracts remain compatible.
