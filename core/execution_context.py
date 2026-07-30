"""Immutable execution context for PrimeAIExplorer runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import platform
from typing import Any


RUN_SCHEMA_VERSION = "0.8.0"
PRIME_AI_EXPLORER_VERSION = "0.8.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_run_id(
    sequence: int,
    *,
    run_date: date | None = None,
) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Run sequence must be an integer.")

    if sequence < 1 or sequence > 999_999:
        raise ValueError(
            "Run sequence must be between 1 and 999,999."
        )

    selected_date = run_date or datetime.now(timezone.utc).date()

    return (
        f"RUN-{selected_date.strftime('%Y%m%d')}-"
        f"{sequence:06d}"
    )


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    run_id: str
    experiment_id: str
    experiment_version: str
    dataset_id: str
    dataset_version: str
    prompt_id: str
    prompt_version: str
    connector_id: str
    connector_version: str
    subject_id: str
    model_identifier: str
    execution_mode: str
    output_directory: str
    random_seed: int
    created_at_utc: str
    run_schema_version: str = RUN_SCHEMA_VERSION
    primeaiexplorer_version: str = PRIME_AI_EXPLORER_VERSION

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        experiment_id: str,
        experiment_version: str,
        dataset_id: str,
        dataset_version: str,
        prompt_id: str,
        prompt_version: str,
        connector_id: str,
        connector_version: str,
        subject_id: str,
        model_identifier: str,
        execution_mode: str,
        results_root: str | Path,
        random_seed: int,
        run_date: date | None = None,
    ) -> "ExecutionContext":
        run_id = canonical_run_id(
            sequence,
            run_date=run_date,
        )
        output_directory = str(
            Path(results_root).resolve() / run_id
        )

        return cls(
            run_id=run_id,
            experiment_id=experiment_id,
            experiment_version=experiment_version,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            connector_id=connector_id,
            connector_version=connector_version,
            subject_id=subject_id,
            model_identifier=model_identifier,
            execution_mode=execution_mode,
            output_directory=output_directory,
            random_seed=random_seed,
            created_at_utc=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["environment"] = {
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        }
        return value


__all__ = [
    "ExecutionContext",
    "PRIME_AI_EXPLORER_VERSION",
    "RUN_SCHEMA_VERSION",
    "canonical_run_id",
    "utc_now_iso",
]
