"""Run the free PrimeAIExplorer v0.8 deterministic demonstration."""

from __future__ import annotations

from pathlib import Path

from core.execution_context import ExecutionContext
from core.execution_engine import (
    ExecutionCase,
    ExecutionEngine,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    context = ExecutionContext.create(
        sequence=1,
        experiment_id="EXP-000001",
        experiment_version="0.1.0",
        dataset_id="DS-000001",
        dataset_version="0.1.0",
        prompt_id="PROMPT-000001",
        prompt_version="0.1.0",
        connector_id="CONNECTOR-000001",
        connector_version="0.1.0",
        subject_id="SUBJECT-000001",
        model_identifier="deterministic-mock",
        execution_mode="local",
        results_root=ROOT / "results",
        random_seed=20260725,
    )

    cases = [
        ExecutionCase(
            case_id="CASE-000001",
            condition_id="COND-EXP000001-001",
            record_id="REC-DS000001-0000000001",
            user_prompt=(
                "Prime gaps: 2, 4, 2, 4, 6, 2. "
                "Return a structured prediction."
            ),
        ),
        ExecutionCase(
            case_id="CASE-000002",
            condition_id="COND-EXP000001-002",
            record_id="REC-DS000001-0000000002",
            user_prompt=(
                "Prime gaps: 6, 4, 2, 4, 6, 6. "
                "Return a structured prediction."
            ),
        ),
        ExecutionCase(
            case_id="CASE-000003",
            condition_id="COND-EXP000001-003",
            record_id="REC-DS000001-0000000003",
            user_prompt=(
                "Prime gaps: 4, 2, 4, 2, 10, 2. "
                "Return a structured prediction."
            ),
        ),
    ]

    engine = ExecutionEngine(
        root=ROOT,
        context=context,
    )

    manifest = engine.run(cases)

    print("=" * 72)
    print("PrimeAIExplorer v0.8 - Deterministic Execution Demo")
    print("=" * 72)
    print()
    print(f"Run ID:             {manifest['run_id']}")
    print(f"Status:             {manifest['status']}")
    print(
        "Planned cases:       "
        f"{manifest['accounting']['planned_cases']}"
    )
    print(
        "Executed cases:      "
        f"{manifest['accounting']['executed_cases']}"
    )
    print(
        "Valid evaluations:   "
        f"{manifest['accounting']['valid_evaluations']}"
    )
    print(
        "External access:     "
        f"{manifest['accounting']['external_access_count']}"
    )
    print(
        "Paid calls:          "
        f"{manifest['accounting']['paid_call_count']}"
    )
    print()
    print(f"Output: {context.output_directory}")
    print()
    print("DEMO PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
