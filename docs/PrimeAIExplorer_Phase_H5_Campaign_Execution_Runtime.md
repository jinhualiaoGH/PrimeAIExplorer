# PrimeAIExplorer Phase H5 — Campaign Execution Runtime

## Purpose

Phase H5 executes the immutable H4 `CampaignExecutionPlan`.

H5 is the first Phase H layer that performs runtime work. The scientific
definition, input resolution, case materialization, and execution planning
contracts remain frozen upstream in H1–H4.

## Core components

- `JobExecutionStatus`
- `AttemptOutcome`
- `ExecutionAttempt`
- `JobExecutionRecord`
- `CampaignExecutionRun`
- `CampaignExecutionRuntime`
- `CampaignRunManifest`
- `JobExecutor`

## Executor boundary

The runtime receives a callable:

    executor(job, attempt_index) -> AttemptOutcome

This keeps the H5 runtime provider-neutral. The callable may be backed by the
PrimeAIExplorer provider SDK, the G3 provider-execution bridge, a fixture, a
mock provider, or a later replay engine.

## Retry semantics

Each H4 `ExecutionJob` contains a retry budget.

    maximum attempts = 1 + retry_budget

Success terminates immediately. A non-retryable failure terminates with status
`failed`. Retryable failures continue while budget remains. Exhausting the
budget produces status `exhausted`.

## Exception boundary

Unexpected executor exceptions are converted into non-retryable failed
`AttemptOutcome` records so one provider exception does not destroy campaign
run structure.

## Runtime evidence versus scientific identity

Wall-clock durations are retained as evidence but deliberately excluded from
`record_sha256` and `run_sha256`. Scientifically identical executions therefore
retain the same scientific identity even if latency differs.

Response text, provider request ID, retry history, errors, and attempt metadata
remain part of execution identity.

## Scientific boundary

    H1 defines experiments.
    H2 registers scientific inputs.
    H3 materializes concrete cases.
    H4 plans deterministic execution.
    H5 executes the plan and records outcomes.
    H6 will persist campaign evidence and provenance bundles.

H5 does not alter H1–H4 identities.
