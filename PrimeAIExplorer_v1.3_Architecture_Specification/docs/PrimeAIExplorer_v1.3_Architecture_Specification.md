# PrimeAIExplorer v1.3 Architecture Specification

**Release family:** PrimeAIExplorer v1.3  
**Primary experiment:** EXP-000003 — Prime Value Observatory  
**Status:** Implementation specification  
**Baseline:** PrimeAIExplorer v1.2.2  
**Core principle:** Add scientific capability without modifying the stable execution engine.

---

## 1. Purpose

PrimeAIExplorer v1.3 introduces the first production scientific sequence plugin built on
the generic sequence framework stabilized in v1.2.2.

The release adds a canonical **Prime Value** benchmark:

```text
Observed consecutive prime values
            ↓
Predict the next prime value
```

PrimeNet remains the authoritative mathematical data source. PrimeAIExplorer remains
a read-only experimental consumer.

The v1.3 release must prove that the v1.2 plugin architecture can support a new
scientific benchmark without changes to:

- connector abstractions,
- execution engine contracts,
- observation persistence,
- evaluation persistence,
- report identity rules,
- request identifiers,
- run identifiers,
- existing EXP-000001 and EXP-000002 behavior.

---

## 2. Release objectives

PrimeAIExplorer v1.3 shall:

1. implement a production-grade `PrimeValueSequencePlugin`;
2. define EXP-000003 declaratively;
3. generate a canonical Prime Value dataset from PrimeNet;
4. generate deterministic train, pilot, and evaluation cases;
5. generate blind prompts that do not disclose hidden target values;
6. evaluate exactness, numerical error, and primality validity;
7. preserve reproducibility through hashes and metadata;
8. preserve the complete v1.2.2 regression suite;
9. add focused scientific and integration tests;
10. provide a dry-run pipeline before any large dataset build.

---

## 3. Non-goals

v1.3 does not include:

- Prime Gap Observatory;
- Prime Square Observatory;
- Prime Cube Observatory;
- OEIS ingestion;
- arbitrary external datasets;
- model fine-tuning;
- automatic paid-model execution;
- changes to PrimeNet storage;
- changes to the existing Left Twin scientific definition;
- new connector protocols;
- changes to the report hash contract.

These remain future releases.

---

## 4. System boundary

```text
                     PrimeNet
             Canonical prime repository
                       │
                       │ read-only
                       ▼
          PrimeValueSequencePlugin
                       │
            dataset + metadata
                       ▼
              EXP-000003 cases
                       │
                 blind prompts
                       ▼
           PrimeAIExplorer connectors
                       │
                  observations
                       ▼
                  evaluation
                       │
             scientific summaries
```

### 4.1 PrimeNet responsibilities

PrimeNet owns:

- canonical prime values;
- partition ordering;
- repository integrity;
- range adjacency;
- storage types;
- repository manifests;
- repository checksums.

### 4.2 PrimeAIExplorer responsibilities

PrimeAIExplorer owns:

- sequence-plugin behavior;
- experiment configuration;
- dataset extraction;
- case generation;
- prompt generation;
- connector execution;
- response capture;
- evaluation;
- scientific reporting.

### 4.3 Prohibited coupling

PrimeAIExplorer must not:

- modify PrimeNet files;
- assume filesystem enumeration order;
- reinterpret partition ownership;
- silently skip malformed partitions;
- infer missing repository values;
- rebuild PrimeNet manifests;
- mix source validation with source mutation.

---

## 5. Scientific definition

Let:

```text
p(1), p(2), p(3), ...
```

denote consecutive prime values in increasing order.

For a window size `w` and target endpoint `e`, the absolute observation is:

```text
p(e-w), p(e-w+1), ..., p(e-1)
```

and the target is:

```text
p(e)
```

The primary v1.3 task is:

```text
Given w consecutive prime values, predict the next prime value.
```

### 5.1 Canonical index convention

EXP-000003 configuration and persisted scientific metadata shall use:

```text
one-based prime indices
```

Internal NumPy slicing may use zero-based indices, but every persisted case must contain:

```text
observation_start_index_1_based
observation_end_index_1_based
target_index_1_based
```

The conversion must be explicit and covered by tests.

### 5.2 Initial representations

v1.3 production support:

```text
absolute
```

Framework compatibility may retain:

```text
gaps
combined
```

but EXP-000003 shall initially use only `absolute`.

Normalized, logarithmic, residual, binary, and digit representations are deferred.

---

## 6. Prime Value plugin contract

Canonical class:

```python
class PrimeValueSequencePlugin(SequencePlugin):
    plugin_id = "prime_value"
    plugin_version = "1.3.0"
    display_name = "Prime Values"
    supported_representations = ("absolute",)
```

Required behavior:

```python
validate_source(...)
build_dataset(...)
validate_dataset(...)
load_values(...)
generate_cases(...)
render_prompt(...)
evaluate_prediction(...)
is_structurally_valid(...)
```

### 6.1 Configuration model

The plugin shall accept the complete experiment configuration.

It must not depend on module-level global state.

Recommended pattern:

```python
plugin = PrimeValueSequencePlugin(config)
```

or:

```python
plugin = PrimeValueSequencePlugin().configure(config)
```

### 6.2 Source validation

`validate_source()` must be read-only and return at least:

```json
{
  "plugin_id": "prime_value",
  "plugin_version": "1.3.0",
  "prime_root": "...",
  "partition_count": 300,
  "available_prime_count": 108340298703,
  "required_prime_count": 100000001,
  "sufficient": true,
  "first_prime": 2,
  "last_available_prime": 2999999999989,
  "source_manifest": "...",
  "source_manifest_sha256": "..."
}
```

Validation must confirm:

- source root exists;
- at least one canonical partition exists;
- partitions are numerically ordered;
- partition ranges are adjacent;
- arrays are one-dimensional;
- arrays use an unsigned integer dtype;
- values are strictly increasing within partitions;
- boundary values are strictly increasing across partitions;
- available count is sufficient.

### 6.3 Dataset construction

Dataset construction must:

- read PrimeNet in numeric partition order;
- copy exactly the configured number of prime values;
- preserve prime ordering;
- use canonical unsigned 64-bit storage;
- write atomically;
- refuse replacement unless overwrite is explicit;
- produce metadata only after successful dataset completion;
- remove temporary artifacts after failure;
- never mutate the PrimeNet source.

Canonical output:

```text
experiments/EXP-000003/data/prime_values.npy
experiments/EXP-000003/data/prime_values.metadata.json
```

### 6.4 Dataset count

Recommended initial target:

```text
100,000,001 prime values
```

Rationale:

- 100,000,000 values are available for observations and targets;
- one final value is available as a held-out target;
- the scale is large enough for controlled sampling;
- the dataset remains manageable as uint64.

The final count shall remain configuration-driven.

### 6.5 Dataset validation

`validate_dataset()` must verify:

- file exists;
- array is one-dimensional;
- dtype is canonical;
- count matches configuration;
- first value is `2`;
- values are strictly increasing;
- every sampled value is prime;
- metadata file exists;
- metadata dataset hash matches;
- held-out target exists;
- no duplicate values exist.

Full primality testing of every value is not required when the dataset is copied from a
verified PrimeNet repository. Deterministic sampling must be used and recorded.

### 6.6 Structural validity

A prediction is structurally valid when:

```text
prediction is an integer
prediction > 1
prediction is prime
```

The deterministic 64-bit primality implementation already verified in
`plugins.left_twin.is_prime_64` shall remain the canonical primality backend for values
within uint64 range.

Boolean values must be rejected.

---

## 7. EXP-000003 configuration

Canonical location:

```text
experiments/EXP-000003/config/experiment.json
```

Minimum structure:

```json
{
  "schema_version": "1.0",
  "experiment": {
    "id": "EXP-000003",
    "name": "Prime Value Observatory",
    "version": "1.3.0",
    "status": "planned"
  },
  "plugin": {
    "id": "prime_value",
    "version": "1.3.0"
  },
  "repository": {
    "prime_root": "E:/PrimeNet/Repository/ranges",
    "manifest": "E:/PrimeNet/Repository/metadata/repository_manifest.csv",
    "read_only": true
  },
  "sequence": {
    "representation": "absolute",
    "target_count": 100000001,
    "dataset_file": "data/prime_values.npy",
    "metadata_file": "data/prime_values.metadata.json"
  },
  "cases": {
    "window_sizes": [4, 8, 16, 32, 64],
    "case_count_per_window": 100,
    "sampling_seed": 130003,
    "minimum_target_index_1_based": 1000,
    "maximum_target_index_1_based": 100000001
  },
  "prompts": {
    "disclose_sequence_name": false,
    "response_format": "json_prediction_v1"
  },
  "evaluation": {
    "require_integer": true,
    "require_prime_for_structural_validity": true
  }
}
```

All paths shall be resolved relative to `_experiment_root` unless explicitly absolute.

---

## 8. Dataset metadata schema

Canonical metadata fields:

```json
{
  "schema_version": "1.0",
  "experiment_id": "EXP-000003",
  "plugin_id": "prime_value",
  "plugin_version": "1.3.0",
  "representation": "absolute",
  "source_type": "primenet_prime_repository",
  "source_root": "...",
  "source_manifest": "...",
  "source_manifest_sha256": "...",
  "dataset_file": "prime_values.npy",
  "dataset_sha256": "...",
  "dtype": "uint64",
  "count": 100000001,
  "first_value": 2,
  "last_observation_value": 2038074739,
  "held_out_target_value": 2038074751,
  "held_out_target_index_1_based": 100000001,
  "build_started_utc": "...",
  "build_completed_utc": "...",
  "builder_version": "1.3.0",
  "validation": {
    "strictly_increasing": true,
    "sampled_primality_count": 1000,
    "sampled_primality_passed": true
  }
}
```

Timestamps are informational and must not participate in stable scientific identity hashes
unless the existing framework explicitly requires them.

---

## 9. Case-generation contract

### 9.1 Determinism

Given the same:

- dataset hash,
- experiment configuration,
- sampling seed,
- window sizes,
- case count,

the generated case set must be byte-for-byte reproducible.

### 9.2 Leakage prevention

A case must never include its target in:

- observation values;
- prompt text;
- public case JSON;
- filename;
- explanatory metadata delivered to a connector.

Private answer keys may contain targets.

### 9.3 Case identity

Recommended case ID:

```text
CASE-W004-000001
CASE-W008-000001
CASE-W016-000001
CASE-W032-000001
CASE-W064-000001
```

### 9.4 Case record

Private canonical record:

```json
{
  "case_id": "CASE-W008-000001",
  "experiment_id": "EXP-000003",
  "plugin_id": "prime_value",
  "representation": "absolute",
  "window_size": 8,
  "observation_start_index_1_based": 993,
  "observation_end_index_1_based": 1000,
  "target_index_1_based": 1001,
  "observation": [7817, 7823, 7829, 7841, 7853, 7867, 7873, 7877],
  "target": 7879,
  "dataset_sha256": "...",
  "case_sha256": "..."
}
```

Public prompt inputs shall omit `target`.

### 9.5 Sampling rules

Target indices must:

- exceed the window size;
- remain within dataset bounds;
- be unique within each window group unless repetition is explicitly configured;
- be selected with a fixed seed;
- avoid the first small-prime region by using a configured minimum index;
- include an optional deterministic boundary sample.

---

## 10. Prompt contract

Canonical blind prompt:

```text
SYSTEM
You are participating in a controlled numerical continuation experiment.
Follow the response format exactly.

USER
You are given a sequence of consecutive integer values.

Observation window size: 8

Observed values:
7817 7823 7829 7841 7853 7867 7873 7877

Predict the next value.

Return JSON only using this exact structure:

{
  "prediction": <integer>,
  "confidence": <integer from 0 to 100>,
  "explanation": "<brief explanation>"
}
```

By default, the prompt shall not disclose:

- that the sequence contains primes;
- the source repository;
- the target index;
- the target value;
- structural validity rules.

A disclosed-sequence experimental arm may be added later as a separate condition.

---

## 11. Response parsing

The canonical response parser shall:

- require a JSON object;
- require `prediction`;
- require integer prediction;
- reject booleans;
- accept confidence only in `[0, 100]`;
- preserve explanation as text;
- record malformed responses without inventing values;
- never silently coerce floating-point values to integers.

A numeric string may be accepted only if the existing evaluation policy explicitly allows it.

---

## 12. Evaluation metrics

Required per-case metrics:

```text
exact_match
absolute_error
relative_error
signed_error
structurally_valid
is_prime_prediction
confidence
latency_ms
response_valid_json
response_schema_valid
```

### 12.1 Exact match

```text
prediction == target
```

### 12.2 Absolute error

```text
abs(prediction - target)
```

### 12.3 Relative error

```text
abs(prediction - target) / target
```

### 12.4 Signed error

```text
prediction - target
```

### 12.5 Structural validity

```text
prediction is a prime integer
```

### 12.6 Aggregate metrics

Reports shall include:

- exact accuracy;
- mean absolute error;
- median absolute error;
- mean relative error;
- median relative error;
- prime-valid prediction rate;
- valid JSON rate;
- schema-valid response rate;
- average confidence;
- confidence calibration summaries;
- latency summaries;
- metrics by window size;
- metrics by connector;
- metrics by model;
- metrics by experiment condition.

---

## 13. Registry requirements

The sequence plugin registry shall contain:

```text
prime_value
module = sequence_plugins.builtin.prime_value
class = PrimeValueSequencePlugin
version = 1.3.0
status = Active
source_type = primenet_repository
```

CSV and JSON registries must agree exactly.

The experiment registry shall add EXP-000003 without altering EXP-000001 or EXP-000002.

Duplicate IDs must remain errors.

---

## 14. Command-line lifecycle

Recommended commands:

```powershell
py .\run_experiment.py `
    validate-source `
    --experiment EXP-000003

py .\run_experiment.py `
    build-dataset `
    --experiment EXP-000003

py .\run_experiment.py `
    validate-dataset `
    --experiment EXP-000003

py .\run_experiment.py `
    generate-cases `
    --experiment EXP-000003

py .\run_experiment.py `
    generate-prompts `
    --experiment EXP-000003

py .\run_experiment.py `
    generate-baselines `
    --experiment EXP-000003

py .\run_experiment.py `
    summarize `
    --experiment EXP-000003
```

A dry-run command must be available before dataset construction:

```powershell
py .\run_experiment.py `
    pipeline `
    --experiment EXP-000003 `
    --dry-run
```

---

## 15. Baselines

Minimum deterministic baselines:

### Last value

```text
prediction = last observed prime
```

Expected to be structurally valid but never exact for strictly increasing sequences.

### Last value plus last gap

```text
prediction = p(n) + (p(n) - p(n-1))
```

### Median recent gap

```text
prediction = p(n) + median(recent prime gaps)
```

### Modal recent gap

```text
prediction = p(n) + mode(recent prime gaps)
```

### Next-prime corrected baseline

```text
candidate = arithmetic baseline
prediction = first prime >= candidate
```

The next-prime-corrected baseline must be reported separately because it uses explicit
primality knowledge.

All baselines must be deterministic.

---

## 16. Reproducibility and identity

The following hashes shall be recorded:

```text
source manifest SHA-256
dataset SHA-256
configuration SHA-256
case SHA-256
prompt SHA-256
request SHA-256
response SHA-256
evaluation SHA-256
report SHA-256
```

Hash inputs must use canonical JSON serialization with:

- UTF-8;
- sorted keys;
- stable separators;
- no timestamp fields unless contractually required;
- normalized path handling where applicable.

---

## 17. Test requirements

v1.3 cannot be released unless all existing v1.2.2 tests pass.

New focused tests shall cover:

### Plugin contract

- registry loads Prime Value plugin;
- plugin metadata matches registry;
- inactive plugins remain rejected;
- source validation is read-only;
- insufficient source count is rejected.

### Dataset construction

- synthetic repository extraction;
- numeric partition ordering;
- cross-partition monotonicity;
- exact target count;
- atomic write behavior;
- overwrite protection;
- temporary-file cleanup;
- metadata hash agreement.

### Dataset validation

- first value equals `2`;
- strictly increasing values;
- duplicate rejection;
- non-prime sample rejection;
- wrong dtype rejection;
- metadata mismatch rejection.

### Case generation

- one-based index correctness;
- exact observation length;
- target exclusion;
- deterministic sampling;
- unique case IDs;
- boundary cases;
- reproducible case hashes.

### Prompt generation

- no target leakage;
- no sequence-name disclosure by default;
- exact JSON response contract;
- deterministic prompt hash.

### Evaluation

- exact prediction;
- incorrect prime prediction;
- composite prediction;
- boolean rejection;
- malformed JSON;
- confidence range validation;
- absolute and relative error.

### Compatibility

- EXP-000001 unchanged;
- EXP-000002 unchanged;
- legacy primality alias retained;
- full connector suite passes;
- full execution-engine suite passes;
- full report suite passes.

Target minimum after integration:

```text
110 or more passing tests
```

The exact count is less important than complete coverage and zero failures.

---

## 18. Installation and release safety

The v1.3 installer must:

1. require baseline version `1.2.2`;
2. create a timestamped backup;
3. install files;
4. update VERSION only within the controlled transaction;
5. run syntax validation;
6. run focused v1.3 tests;
7. run the complete regression suite;
8. check `$LASTEXITCODE` after every Python invocation;
9. report success only after all checks pass;
10. print the backup path on both success and failure.

A failed installer must never print a success message.

---

## 19. Versioning policy

Recommended sequence:

```text
v1.3.0-rc1  implementation candidate
v1.3.0      production Prime Value release
```

Maintenance releases shall be used only for defects:

```text
v1.3.1
v1.3.2
```

Future scientific plugins should not be bundled into Prime Value maintenance releases.

---

## 20. Implementation phases

### Phase A — Contract and configuration

Deliver:

- final `PrimeValueSequencePlugin` contract;
- EXP-000003 configuration;
- registry updates;
- JSON schemas;
- dry-run validation.

Exit criterion:

```text
configuration and source validation tests pass
```

### Phase B — Dataset engine

Deliver:

- PrimeNet partition reader;
- atomic Prime Value dataset builder;
- metadata generator;
- dataset validator.

Exit criterion:

```text
synthetic and bounded real-source dataset tests pass
```

### Phase C — Cases and prompts

Deliver:

- deterministic endpoint sampling;
- private answer keys;
- public case files;
- blind prompts;
- prompt hashes.

Exit criterion:

```text
zero target leakage and deterministic reproduction
```

### Phase D — Evaluation and baselines

Deliver:

- Prime Value structural validity;
- numerical metrics;
- deterministic baselines;
- aggregate summaries.

Exit criterion:

```text
focused scientific evaluation tests pass
```

### Phase E — Full integration

Deliver:

- command routing;
- installer;
- validator;
- documentation;
- full regression run.

Exit criterion:

```text
all tests pass and Git release is clean
```

---

## 21. Acceptance criteria

PrimeAIExplorer v1.3.0 is accepted only when:

```text
[PASS] Baseline version was v1.2.2
[PASS] PrimeNet source validation passed
[PASS] Prime Value dataset built atomically
[PASS] Dataset metadata hash matched
[PASS] Case generation was deterministic
[PASS] No prompt leaked a target
[PASS] Structural primality evaluation passed
[PASS] EXP-000001 regression passed
[PASS] EXP-000002 regression passed
[PASS] Complete test suite passed
[PASS] VERSION equals 1.3.0
[PASS] Git diff check passed
[PASS] Main branch pushed
[PASS] v1.3.0 tag pushed
```

---

## 22. Paper 2 alignment

The implementation evidence generated by v1.3 should support:

> **PrimeAIExplorer: A Reproducible Framework for Evaluating AI Models on Structured Mathematical Sequences**

Direct evidence mapping:

```text
Plugin architecture        → Section 4
Experiment configuration   → Section 5
Connector abstraction      → Section 6
Reproducibility            → Section 7
Prime Value benchmark      → Section 8
Left Twin benchmark        → Section 9
Validation and testing     → Section 10
```

The software release and manuscript should use the same terminology.

---

## 23. Final architectural rule

> PrimeNet defines and validates mathematical data.  
> Sequence plugins expose mathematical experiments.  
> PrimeAIExplorer executes, evaluates, and reports those experiments.  
> No layer silently assumes responsibilities owned by another layer.
