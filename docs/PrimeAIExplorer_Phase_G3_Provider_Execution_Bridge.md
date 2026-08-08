# PrimeAIExplorer Phase G3 — Provider Execution Bridge

## Purpose

Phase G3 connects the canonical Phase F2 provider SDK to the frozen G1/G2
behavioral observation contracts.

## Boundary

```text
TrialSpec
   |
   v
BehavioralRequestSpec
   |
   v
F2 ModelRequest
   |
   v
ModelProvider.generate()
   |
   +-- ProviderResponse --> caller-supplied EvaluationOutcome
   |                         |
   |                         v
   |                  BehavioralEvaluationRecord
   |
   +-- Exception --------> provider_error + not_evaluated
```

## Design rules

1. G3 performs exactly one provider invocation per `execute()` call.
2. G3 does not define semantic evaluator policy.
3. Successful provider responses are evaluated only through a caller-supplied
   `EvaluationOutcome` builder.
4. Provider/API exceptions never become model score zero.
5. Provider and model identity in `ProviderResponse` must match `TrialSpec`.
6. F2 latency, request ID, finish reason, usage, and provider metadata are
   preserved.
7. Response text receives a deterministic SHA-256 identity.
8. `execute_into()` can append only currently missing trials to a G2 ledger.
9. Retry policy, repeated scheduling, semantic evaluator routing, metrics,
   fingerprints, and dashboards remain outside G3.

## Phase relationship

- F2: provider transport and SDK
- G1: behavioral evaluation contracts
- G2: repeated-trial observation planning and ledger
- G3: provider execution bridge
