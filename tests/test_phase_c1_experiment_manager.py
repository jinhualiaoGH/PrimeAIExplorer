from __future__ import annotations

import hashlib
import json

import pytest

from experiment_manager import (
    ExperimentManager,
    ExperimentRecord,
    ExperimentSpecification,
    ExperimentStatus,
)


def make_specification(case_count: int = 2) -> ExperimentSpecification:
    return ExperimentSpecification(
        name="Deterministic prime-gap pilot",
        sequence_plugin="primenet.gaps",
        sequence_parameters={
            "repository": "fixture",
            "start_index": 1000,
        },
        window_sizes=(4, 8, 16),
        case_count=case_count,
        prompt_template="prime-gap-next-v1",
        model_provider="manual",
        model_name="controlled-test",
        model_parameters={"temperature": 0},
        random_seed=20260801,
    )


def make_record(case_number: int) -> ExperimentRecord:
    prompt_text = f"case-{case_number}"

    return ExperimentRecord(
        case_id=f"CASE-{case_number:06d}",
        sequence_index=1000 + case_number,
        window_size=8,
        prompt_sha256=hashlib.sha256(
            prompt_text.encode("utf-8")
        ).hexdigest(),
        response_text=json.dumps(
            {
                "prediction": 6,
                "confidence": 25,
                "explanation": "test",
            }
        ),
        parsed_prediction=6,
        actual_value=6,
        is_correct=True,
        confidence=25,
        latency_seconds=0.1,
    )


def test_experiment_id_is_deterministic(tmp_path):
    manager = ExperimentManager(tmp_path)
    specification = make_specification()

    first_id, first_path = manager.create(specification)
    second_id, second_path = manager.create(specification)

    assert first_id == second_id
    assert first_path == second_path
    assert first_id.startswith("EXP-")


def test_specification_change_changes_identifier(tmp_path):
    manager = ExperimentManager(tmp_path)

    first_id, _ = manager.create(make_specification(case_count=2))
    second_id, _ = manager.create(make_specification(case_count=3))

    assert first_id != second_id


def test_run_checkpoint_and_completion(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())

    state = manager.start(experiment_id)
    assert state.status == ExperimentStatus.RUNNING

    checkpoint = manager.append_record(
        experiment_id,
        make_record(0),
    )
    assert checkpoint.next_case_number == 1
    assert checkpoint.completed_case_count == 1

    checkpoint = manager.append_record(
        experiment_id,
        make_record(1),
    )
    assert checkpoint.next_case_number == 2
    assert checkpoint.completed_case_count == 2

    state = manager.complete(experiment_id)
    assert state.status == ExperimentStatus.COMPLETED

    summary = manager.summary(experiment_id)
    assert summary["remaining_case_count"] == 0


def test_duplicate_case_is_rejected(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())
    manager.start(experiment_id)

    record = make_record(0)
    manager.append_record(experiment_id, record)

    with pytest.raises(RuntimeError, match="Duplicate"):
        manager.append_record(experiment_id, record)


def test_incomplete_experiment_cannot_complete(tmp_path):
    manager = ExperimentManager(tmp_path)
    experiment_id, _ = manager.create(make_specification())
    manager.start(experiment_id)

    with pytest.raises(RuntimeError, match="Cannot complete"):
        manager.complete(experiment_id)


def test_cli_json_loader_accepts_utf8_bom(tmp_path):
    from experiment_manager.cli import load_json_object

    path = tmp_path / "bom_document.json"
    path.write_text(
        '{"name": "BOM-compatible"}',
        encoding="utf-8-sig",
    )

    assert load_json_object(path) == {
        "name": "BOM-compatible",
    }
