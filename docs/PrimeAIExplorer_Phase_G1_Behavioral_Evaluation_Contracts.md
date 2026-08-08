# PrimeAIExplorer Phase G1 — Behavioral Evaluation Contracts

Phase G1 establishes provider-neutral, immutable behavioral evaluation
contracts on top of the canonical Phase F2 provider SDK.

## Invariants

- Provider/API failure is `provider_error + not_evaluated`.
- Provider/API failure never becomes model score zero.
- A completed model execution is `completed + evaluated`.
- Trial identity is explicit.
- Surface answer and semantic answer are separate fields.
- Provider/model/latency/token metadata are preserved.
- Contracts and records are deterministically hashable.
- Phase G1 is additive: it does not modify the Phase F2 provider SDK or
  the existing numerical evaluation engine.

## Phase boundary

G1 defines data contracts and registry behavior only. Repeated-trial
orchestration, semantic evaluator implementations, behavioral statistics,
fingerprints, and observatory views belong to later Phase G increments.
