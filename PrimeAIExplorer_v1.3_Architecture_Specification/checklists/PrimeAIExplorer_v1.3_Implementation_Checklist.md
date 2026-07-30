# PrimeAIExplorer v1.3 Implementation Checklist

## Baseline

- [ ] `VERSION` is exactly `1.2.2`
- [ ] Working tree reviewed
- [ ] Existing 96-test suite passes
- [ ] Timestamped pre-v1.3 backup created

## Phase A — Configuration

- [ ] EXP-000003 directory created
- [ ] `experiment.json` created
- [ ] Prime Value plugin registry row updated to `1.3.0`
- [ ] CSV and JSON registries agree
- [ ] Source paths are configuration-driven
- [ ] Dry-run command implemented
- [ ] Source validation is read-only

## Phase B — Dataset

- [ ] Numeric partition ordering implemented
- [ ] Partition adjacency validated
- [ ] Dataset count configuration-driven
- [ ] Atomic `.tmp` write implemented
- [ ] Overwrite requires explicit flag
- [ ] Metadata written after dataset success
- [ ] Dataset SHA-256 recorded
- [ ] Source manifest SHA-256 recorded
- [ ] Temporary artifacts cleaned after failure

## Phase C — Cases

- [ ] One-based scientific indices persisted
- [ ] Zero-based slicing tested
- [ ] Fixed sampling seed used
- [ ] Case IDs unique
- [ ] Targets excluded from public case files
- [ ] Answer keys stored separately
- [ ] Case hashes deterministic
- [ ] Window sizes 4, 8, 16, 32, 64 supported

## Phase D — Prompts and evaluation

- [ ] Blind prompt hides sequence identity
- [ ] JSON-only response contract retained
- [ ] Prompt hashes deterministic
- [ ] Integer prediction required
- [ ] Boolean predictions rejected
- [ ] Primality validity evaluated
- [ ] Exact, absolute, relative, and signed errors recorded
- [ ] Confidence range validated
- [ ] Baselines deterministic

## Phase E — Release

- [ ] Focused v1.3 tests pass
- [ ] Existing v1.2.2 tests pass
- [ ] Full regression suite passes
- [ ] Installer checks every exit code
- [ ] Installer cannot report false success
- [ ] `VERSION` is `1.3.0`
- [ ] `git diff --check` passes
- [ ] Release commit created
- [ ] Annotated `v1.3.0` tag created
- [ ] Main and tag pushed
