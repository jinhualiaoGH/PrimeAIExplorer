from __future__ import annotations

from pathlib import Path

import pytest

from pipeline_scheduler.models import ScheduledStage, SchedulerSpecification
from pipeline_scheduler.scheduler import DependencyScheduler, SchedulerError, StageExecution


def spec(*stages: ScheduledStage) -> SchedulerSpecification:
    return SchedulerSpecification(name="test", stages=tuple(stages), max_parallel=2)


def ok(stage: ScheduledStage) -> StageExecution:
    return StageExecution(stage.name, 0, f"completed {stage.name}", "")


def test_topological_order_is_deterministic(tmp_path: Path) -> None:
    scheduler = DependencyScheduler(
        spec(
            ScheduledStage("report", ("report",), ("metrics",)),
            ScheduledStage("fixture", ("fixture",)),
            ScheduledStage("metrics", ("metrics",), ("fixture",)),
        ),
        tmp_path / "state.json",
    )
    assert scheduler.topological_order() == ["fixture", "metrics", "report"]


def test_cycle_detection(tmp_path: Path) -> None:
    with pytest.raises(SchedulerError, match="cycle"):
        DependencyScheduler(
            spec(
                ScheduledStage("a", ("a",), ("b",)),
                ScheduledStage("b", ("b",), ("a",)),
            ),
            tmp_path / "state.json",
        )


def test_missing_dependency_detection(tmp_path: Path) -> None:
    with pytest.raises(SchedulerError, match="missing dependencies"):
        DependencyScheduler(
            spec(ScheduledStage("a", ("a",), ("missing",))),
            tmp_path / "state.json",
        )


def test_successful_run(tmp_path: Path) -> None:
    scheduler = DependencyScheduler(
        spec(
            ScheduledStage("a", ("a",)),
            ScheduledStage("b", ("b",), ("a",)),
        ),
        tmp_path / "state.json",
    )
    summary = scheduler.run(executor=ok)
    assert summary["status"] == "completed"
    assert summary["counts"] == {"completed": 2}


def test_failure_blocks_dependents(tmp_path: Path) -> None:
    scheduler = DependencyScheduler(
        spec(
            ScheduledStage("a", ("a",)),
            ScheduledStage("b", ("b",), ("a",)),
        ),
        tmp_path / "state.json",
    )

    def fail_first(stage: ScheduledStage) -> StageExecution:
        return StageExecution(stage.name, 1 if stage.name == "a" else 0, "", "boom")

    summary = scheduler.run(executor=fail_first)
    assert summary["status"] == "failed"
    assert summary["counts"] == {"blocked": 1, "failed": 1}


def test_pause_and_resume(tmp_path: Path) -> None:
    scheduler = DependencyScheduler(
        spec(
            ScheduledStage("a", ("a",)),
            ScheduledStage("b", ("b",), ("a",)),
            ScheduledStage("c", ("c",), ("b",)),
        ),
        tmp_path / "state.json",
    )
    first = scheduler.run(executor=ok, max_stages=1)
    assert first["status"] == "paused"
    second = scheduler.run(executor=ok)
    assert second["status"] == "completed"
    assert second["counts"] == {"completed": 3}
