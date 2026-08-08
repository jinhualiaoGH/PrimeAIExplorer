# PrimeAIExplorer Phase G4 — Semantic Evaluator Router

## Purpose

Phase G4 introduces provider-independent semantic evaluation routing on top of
the frozen G1/G2/G3 contracts.

## Architecture

```text
ProviderResponse
      |
      v
BehavioralEvaluationContract.evaluator_id
      |
      v
SemanticEvaluatorRouter
      |
      +--> ExactIntegerEvaluator
      +--> ExactTextEvaluator
      +--> StructuredPredictionEvaluator
      |
      v
EvaluationOutcome
      |
      v
G3 BehavioralProviderExecutionBridge
      |
      v
BehavioralEvaluationRecord
```

## Rules

1. Routing is driven by the immutable G1 `evaluator_id`.
2. G4 never invokes providers.
3. G4 never converts provider exceptions into evaluation failures.
4. A semantically wrong but valid provider response is an evaluated model
   failure, not a provider error.
5. A G4 `EvaluationOutcome` is directly compatible with the G3 outcome-builder
   contract.
6. Evaluators preserve surface and semantic answers separately.
7. Contract identity and SHA-256 are attached to evaluation metadata.
8. Unknown evaluator IDs fail explicitly.
9. Evaluator registration is deterministic and duplicate-safe.

## Initial evaluator set

- `numeric_exact`
- `text_exact`
- `structured_prediction`

The registry is intentionally extensible so later phases can add SQL, JSON
semantic equivalence, normalized time, sequence prediction, and domain-specific
PrimeNet evaluators without changing provider execution code.

## Phase boundary

Behavioral statistics, entropy, consistency, calibration, cross-model
agreement, and fingerprint construction remain outside G4.
