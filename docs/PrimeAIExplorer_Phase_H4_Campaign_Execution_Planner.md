# PrimeAIExplorer Phase H4 — Campaign Execution Planner

## Purpose

Phase H4 transforms immutable H3 materialized cases into a deterministic
execution plan.

H4 plans execution structure. It does not execute providers.

## Core components

- `PlanningPolicy`
- `ExecutionJob`
- `ExecutionBatch`
- `CampaignExecutionPlan`
- `CampaignExecutionPlanner`
- `ExecutionPlanManifest`

## Planning contract

The planner consumes:

- an H1 `ExperimentDefinition`,
- an H3 `ExperimentMaterialization`,
- an H1 `ExecutionPolicy`,
- an H4 `PlanningPolicy`.

It emits deterministic execution jobs and batches.

## Execution jobs

Every H4 job preserves the identity of its H3 case and adds execution-planning
metadata:

- job ordinal,
- lane assignment,
- batch assignment,
- retry budget,
- timeout,
- provider/model identity,
- seed.

The job does not contain provider responses.

## Concurrency lanes

The planner creates stable logical lanes:

    LANE-001
    LANE-002
    ...

Jobs are assigned round-robin to lanes after deterministic case ordering.

These lanes describe concurrency structure only; H5 will decide how workers
realize that structure at runtime.

## Batches

Jobs are divided into deterministic batches:

    BATCH-00001
    BATCH-00002
    ...

Batch size is controlled by `PlanningPolicy.batch_size`.

## Provider affinity

When `preserve_provider_affinity=True`, cases are ordered by provider/model
target before record/repetition identity. This supports efficient provider-aware
execution without changing H3 scientific case identities.

When disabled, cases are ordered by H3 case ID.

## Retry and timeout policy

By default, retry budgets and timeouts are inherited from the H1 `TrialPolicy`.

H4 may explicitly override them through `PlanningPolicy`.

The resulting values become part of the deterministic execution-plan identity.

## Scientific boundary

    H1 defines experiments.
    H2 registers scientific inputs.
    H3 materializes exact cases.
    H4 plans deterministic execution.
    H5 will execute the plan.

No provider/API calls are made in H4.
