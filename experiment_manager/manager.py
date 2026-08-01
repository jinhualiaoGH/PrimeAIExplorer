"""Deterministic experiment creation and lifecycle management."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import (
    ExperimentCheckpoint,
    ExperimentRecord,
    ExperimentSpecification,
    ExperimentState,
    ExperimentStatus,
)
from .storage import (
    append_jsonl,
    atomic_write_json,
    canonical_json_bytes,
    read_json,
    read_jsonl,
)


def utc_now_text() -> str:
    """Return a stable ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ExperimentManager:
    """Manage deterministic experiment directories.

    Scientific configuration is immutable after creation. Runtime state,
    checkpoints, and append-only response records are stored separately.
    """

    SPEC_FILENAME = "experiment.json"
    STATE_FILENAME = "state.json"
    CHECKPOINT_FILENAME = "checkpoints/checkpoint.json"
    RESULTS_FILENAME = "results/responses.jsonl"

    def __init__(self, root: str | Path = "experiments") -> None:
        self.root = Path(root).resolve()

    @staticmethod
    def compute_experiment_id(
        specification: ExperimentSpecification,
    ) -> str:
        """Calculate the deterministic experiment identifier."""

        digest = hashlib.sha256(
            canonical_json_bytes(specification.to_dict())
        ).hexdigest()

        return f"EXP-{digest[:16].upper()}"

    def experiment_path(self, experiment_id: str) -> Path:
        self._validate_experiment_id(experiment_id)
        return self.root / experiment_id

    def create(
        self,
        specification: ExperimentSpecification,
    ) -> tuple[str, Path]:
        """Create an experiment or validate an identical existing one."""

        experiment_id = self.compute_experiment_id(specification)
        directory = self.experiment_path(experiment_id)
        specification_path = directory / self.SPEC_FILENAME
        state_path = directory / self.STATE_FILENAME
        checkpoint_path = directory / self.CHECKPOINT_FILENAME

        directory.mkdir(parents=True, exist_ok=True)
        (directory / "results").mkdir(exist_ok=True)
        (directory / "checkpoints").mkdir(exist_ok=True)
        (directory / "logs").mkdir(exist_ok=True)

        new_specification = {
            "experiment_id": experiment_id,
            "specification": specification.to_dict(),
        }

        if specification_path.exists():
            existing = read_json(specification_path)

            if existing != new_specification:
                raise RuntimeError(
                    f"Experiment identifier collision at {specification_path}."
                )
        else:
            atomic_write_json(specification_path, new_specification)

        if not state_path.exists():
            now = utc_now_text()
            state = ExperimentState(
                experiment_id=experiment_id,
                status=ExperimentStatus.CREATED,
                created_at_utc=now,
                updated_at_utc=now,
            )
            atomic_write_json(state_path, state.to_dict())

        if not checkpoint_path.exists():
            checkpoint = ExperimentCheckpoint(
                next_case_number=0,
                completed_case_count=0,
                failed_case_count=0,
                last_case_id=None,
                updated_at_utc=utc_now_text(),
            )
            atomic_write_json(checkpoint_path, checkpoint.to_dict())

        return experiment_id, directory

    def load_specification(
        self,
        experiment_id: str,
    ) -> ExperimentSpecification:
        document = read_json(
            self.experiment_path(experiment_id) / self.SPEC_FILENAME
        )

        raw = document["specification"]

        return ExperimentSpecification(
            name=str(raw["name"]),
            sequence_plugin=str(raw["sequence_plugin"]),
            sequence_parameters=dict(raw["sequence_parameters"]),
            window_sizes=tuple(int(value) for value in raw["window_sizes"]),
            case_count=int(raw["case_count"]),
            prompt_template=str(raw["prompt_template"]),
            model_provider=str(raw["model_provider"]),
            model_name=str(raw["model_name"]),
            model_parameters=dict(raw.get("model_parameters", {})),
            random_seed=int(raw.get("random_seed", 0)),
            schema_version=str(raw.get("schema_version", "1.0")),
        )

    def load_state(self, experiment_id: str) -> ExperimentState:
        raw = read_json(
            self.experiment_path(experiment_id) / self.STATE_FILENAME
        )

        return ExperimentState(
            experiment_id=str(raw["experiment_id"]),
            status=ExperimentStatus(str(raw["status"])),
            created_at_utc=str(raw["created_at_utc"]),
            updated_at_utc=str(raw["updated_at_utc"]),
            started_at_utc=raw.get("started_at_utc"),
            completed_at_utc=raw.get("completed_at_utc"),
            failure_message=raw.get("failure_message"),
        )

    def load_checkpoint(
        self,
        experiment_id: str,
    ) -> ExperimentCheckpoint:
        raw = read_json(
            self.experiment_path(experiment_id)
            / self.CHECKPOINT_FILENAME
        )

        return ExperimentCheckpoint(
            next_case_number=int(raw["next_case_number"]),
            completed_case_count=int(raw["completed_case_count"]),
            failed_case_count=int(raw["failed_case_count"]),
            last_case_id=raw.get("last_case_id"),
            updated_at_utc=str(raw["updated_at_utc"]),
        )

    def start(self, experiment_id: str) -> ExperimentState:
        state = self.load_state(experiment_id)

        if state.status == ExperimentStatus.COMPLETED:
            raise RuntimeError("A completed experiment cannot be restarted.")

        now = utc_now_text()

        updated = replace(
            state,
            status=ExperimentStatus.RUNNING,
            updated_at_utc=now,
            started_at_utc=state.started_at_utc or now,
            completed_at_utc=None,
            failure_message=None,
        )

        self._save_state(updated)
        return updated

    def pause(self, experiment_id: str) -> ExperimentState:
        return self._transition(
            experiment_id,
            ExperimentStatus.PAUSED,
        )

    def complete(self, experiment_id: str) -> ExperimentState:
        specification = self.load_specification(experiment_id)
        checkpoint = self.load_checkpoint(experiment_id)

        if checkpoint.completed_case_count < specification.case_count:
            raise RuntimeError(
                "Cannot complete experiment: "
                f"{checkpoint.completed_case_count}/"
                f"{specification.case_count} cases are complete."
            )

        now = utc_now_text()
        state = self.load_state(experiment_id)

        updated = replace(
            state,
            status=ExperimentStatus.COMPLETED,
            updated_at_utc=now,
            completed_at_utc=now,
            failure_message=None,
        )

        self._save_state(updated)
        return updated

    def fail(
        self,
        experiment_id: str,
        message: str,
    ) -> ExperimentState:
        if not message.strip():
            raise ValueError("Failure message must not be empty.")

        state = self.load_state(experiment_id)

        updated = replace(
            state,
            status=ExperimentStatus.FAILED,
            updated_at_utc=utc_now_text(),
            failure_message=message,
        )

        self._save_state(updated)
        return updated

    def append_record(
        self,
        experiment_id: str,
        record: ExperimentRecord,
        *,
        successful: bool = True,
    ) -> ExperimentCheckpoint:
        """Append a result and advance the durable checkpoint."""

        state = self.load_state(experiment_id)

        if state.status != ExperimentStatus.RUNNING:
            raise RuntimeError(
                "Records may only be appended while an experiment is running."
            )

        checkpoint = self.load_checkpoint(experiment_id)
        specification = self.load_specification(experiment_id)

        if checkpoint.next_case_number >= specification.case_count:
            raise RuntimeError("The experiment already contains all cases.")

        results_path = (
            self.experiment_path(experiment_id) / self.RESULTS_FILENAME
        )

        existing_case_ids = {
            str(item["case_id"])
            for item in read_jsonl(results_path)
        }

        if record.case_id in existing_case_ids:
            raise RuntimeError(
                f"Duplicate experiment case: {record.case_id}"
            )

        append_jsonl(results_path, record.to_dict())

        updated_checkpoint = ExperimentCheckpoint(
            next_case_number=checkpoint.next_case_number + 1,
            completed_case_count=(
                checkpoint.completed_case_count + (1 if successful else 0)
            ),
            failed_case_count=(
                checkpoint.failed_case_count + (0 if successful else 1)
            ),
            last_case_id=record.case_id,
            updated_at_utc=utc_now_text(),
        )

        atomic_write_json(
            self.experiment_path(experiment_id)
            / self.CHECKPOINT_FILENAME,
            updated_checkpoint.to_dict(),
        )

        return updated_checkpoint

    def records(
        self,
        experiment_id: str,
    ) -> Iterable[dict[str, Any]]:
        return read_jsonl(
            self.experiment_path(experiment_id) / self.RESULTS_FILENAME
        )

    def summary(self, experiment_id: str) -> dict[str, Any]:
        specification = self.load_specification(experiment_id)
        state = self.load_state(experiment_id)
        checkpoint = self.load_checkpoint(experiment_id)

        return {
            "experiment_id": experiment_id,
            "directory": str(self.experiment_path(experiment_id)),
            "name": specification.name,
            "status": state.status.value,
            "case_count": specification.case_count,
            "next_case_number": checkpoint.next_case_number,
            "completed_case_count": checkpoint.completed_case_count,
            "failed_case_count": checkpoint.failed_case_count,
            "remaining_case_count": max(
                0,
                specification.case_count
                - checkpoint.completed_case_count
                - checkpoint.failed_case_count,
            ),
            "created_at_utc": state.created_at_utc,
            "started_at_utc": state.started_at_utc,
            "completed_at_utc": state.completed_at_utc,
        }

    def _transition(
        self,
        experiment_id: str,
        status: ExperimentStatus,
    ) -> ExperimentState:
        state = self.load_state(experiment_id)

        if state.status == ExperimentStatus.COMPLETED:
            raise RuntimeError("A completed experiment is immutable.")

        updated = replace(
            state,
            status=status,
            updated_at_utc=utc_now_text(),
        )

        self._save_state(updated)
        return updated

    def _save_state(self, state: ExperimentState) -> None:
        atomic_write_json(
            self.experiment_path(state.experiment_id)
            / self.STATE_FILENAME,
            state.to_dict(),
        )

    @staticmethod
    def _validate_experiment_id(experiment_id: str) -> None:
        if not experiment_id.startswith("EXP-"):
            raise ValueError(
                "Experiment identifiers must begin with 'EXP-'."
            )

        suffix = experiment_id[4:]

        if len(suffix) != 16:
            raise ValueError(
                "Experiment identifiers must contain 16 hash characters."
            )

        try:
            int(suffix, 16)
        except ValueError as exc:
            raise ValueError(
                "Experiment identifier suffix must be hexadecimal."
            ) from exc
