# PrimeAIExplorer Phase G2 — Repeated-Trial Observation Engine

## Status

Phase G2 extends the frozen G1 behavioral evaluation contracts with a
deterministic repeated-trial observation boundary.

## Core invariant

One provider × one model × one case × one trial produces one immutable
observation identity.

## Scope

G2 defines:

- `TrialSpec`
- deterministic observation IDs
- `TrialPlan`
- deterministic trial ordering
- resumable `ObservationLedger`
- conflict-safe ledger merging
- `RepeatedTrialRunManifest`
- aggregation-ready artifacts

## Scientific rules

1. Trial identities must be deterministic.
2. The same plan must produce the same plan hash independent of input ordering.
3. Provider errors are valid observations and retain the G1
   `provider_error + not_evaluated` contract.
4. Duplicate observations are forbidden.
5. Conflicting observations with the same identity are forbidden.
6. Partial ledgers are first-class and expose missing trials for resume.
7. G2 does not compute behavioral statistics, fingerprints, or semantic
   evaluator policy.

## Phase boundary

Provider invocation remains outside this contract package in G2. A future
execution bridge may consume `TrialPlan.iter_trials()` and emit G1
`BehavioralEvaluationRecord` instances into an `ObservationLedger`.

Statistics and behavioral summaries belong to later Phase G increments.
