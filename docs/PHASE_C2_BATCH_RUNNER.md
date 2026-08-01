# PrimeAIExplorer v2.0 Phase C2

## Checkpointed Batch Execution Engine

Phase C2 connects deterministic case plans to the Phase C1 experiment lifecycle.

Core guarantees:

1. Cases execute in deterministic `case_number` order.
2. Resume begins at the C1 checkpoint's `next_case_number`.
3. A result is appended before the checkpoint advances.
4. Duplicate execution is prevented by the C1 duplicate case contract.
5. Dry-run mode performs no state mutation.
6. Exceptions and unsuccessful results follow an explicit retry policy.
7. `KeyboardInterrupt` pauses the experiment without advancing the active case.
8. Per-case failures are isolated unless `stop_on_failure` is enabled.
9. Completed experiments are not executed again.

Executor interface:

```python
def execute(case: BatchCase) -> CaseExecutionResult:
    ...
```

CLI:

```powershell
py -m batch_runner.cli `
    --root .\experiments `
    run `
    .\examples\phase_c2\batch_plan.json `
    --executor batch_runner.demo_executor:execute
```
