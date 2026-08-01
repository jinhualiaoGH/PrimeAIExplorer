from __future__ import annotations

import hashlib

import pytest

from batch_runner import (
    BatchCase,
    BatchPlan,
    BatchRunner,
    CaseExecutionResult,
    RetryPolicy,
)
from experiment_manager import (
    ExperimentManager,
    ExperimentSpecification,
    ExperimentStatus,
)


def make_specification(case_count: int = 3) -> ExperimentSpecification:
    return ExperimentSpecification(
        name="Phase C2 test",
        sequence_plugin="fixture",
        sequence_parameters={},
        window_sizes=(8,),
        case_count=case_count,
        prompt_template="fixture",
        model_provider="fixture",
        model_name="fixture",
        random_seed=20260801,
    )


def make_case(number: int) -> BatchCase:
    text = f"case-{number}"
    return BatchCase(
        case_number=number,
        case_id=f"CASE-{number:06d}",
        sequence_index=1000 + number,
        window_size=8,
        prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        payload={"actual_value": 6},
    )


def make_plan(experiment_id: str, count: int = 3) -> BatchPlan:
    return BatchPlan(
        experiment_id=experiment_id,
        cases=tuple(make_case(number) for number in range(count)),
        retry_policy=RetryPolicy(max_attempts=2),
    )


def successful_executor(case: BatchCase) -> CaseExecutionResult:
    return CaseExecutionResult(
        response_text='{"prediction": 6}',
        parsed_prediction=6,
        actual_value=6,
        is_correct=True,
        confidence=25,
        latency_seconds=0.01,
        successful=True,
    )


def test_batch_run_completes_experiment(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())
    runner = BatchRunner(manager)

    summary = runner.run(make_plan(experiment_id), successful_executor)

    assert summary.completed_count == 3
    assert summary.failed_count == 0
    assert manager.load_checkpoint(experiment_id).next_case_number == 3
    assert manager.load_state(experiment_id).status == ExperimentStatus.COMPLETED


def test_max_cases_pauses_and_resume_continues(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())
    runner = BatchRunner(manager)
    plan = make_plan(experiment_id)

    first = runner.run(plan, successful_executor, max_cases=1)
    assert first.ending_case_number == 1
    assert manager.load_state(experiment_id).status == ExperimentStatus.PAUSED

    second = runner.run(plan, successful_executor)
    assert second.starting_case_number == 1
    assert second.completed_count == 2
    assert manager.load_state(experiment_id).status == ExperimentStatus.COMPLETED


def test_dry_run_does_not_change_state(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())
    runner = BatchRunner(manager)

    summary = runner.run(
        make_plan(experiment_id),
        successful_executor,
        dry_run=True,
    )

    assert summary.dry_run is True
    assert manager.load_checkpoint(experiment_id).next_case_number == 0
    assert manager.load_state(experiment_id).status == ExperimentStatus.CREATED


def test_exception_is_retried(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification(case_count=1))
    runner = BatchRunner(manager, sleep_function=lambda _: None)
    attempts = {"count": 0}

    def flaky(case: BatchCase) -> CaseExecutionResult:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return successful_executor(case)

    summary = runner.run(make_plan(experiment_id, count=1), flaky)

    assert attempts["count"] == 2
    assert summary.completed_count == 1


def test_plan_count_must_match_specification(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification(case_count=3))
    runner = BatchRunner(manager)

    with pytest.raises(RuntimeError, match="case count"):
        runner.run(make_plan(experiment_id, count=2), successful_executor)
