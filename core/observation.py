"""PrimeAIExplorer canonical observation reference implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Mapping


OBSERVATION_SCHEMA_VERSION = "0.3.0"
PRIME_AI_EXPLORER_VERSION = "0.3.0"


class ObservationStatus(StrEnum):
    """Canonical observation lifecycle status."""

    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    REFUSED = "refused"
    INVALID_RESPONSE = "invalid_response"
    CANCELLED = "cancelled"
    CACHED = "cached"
    SUPERSEDED = "superseded"


class EvaluationState(StrEnum):
    """Canonical evaluation state."""

    NOT_STARTED = "not_started"
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    SCORED = "scored"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    EXCLUDED_WITH_REASON = "excluded_with_reason"


def utc_now_iso() -> str:
    """Return a UTC timestamp using a stable ISO 8601 representation."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically for hashing and persistence."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""

    return sha256(value.encode("utf-8")).hexdigest()


def canonical_observation_id(sequence: int) -> str:
    """Convert a positive integer into OBS-NNNNNNNNNN form."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Observation sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Observation sequence must be between 1 and 9,999,999,999."
        )

    return f"OBS-{sequence:010d}"


@dataclass(frozen=True, slots=True)
class ExperimentLink:
    experiment_id: str
    experiment_version: str
    experimental_universe: str
    hypothesis_id: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetLink:
    dataset_id: str
    dataset_version: str
    partition: str
    record_id: str | None = None
    artifact_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class PromptLink:
    prompt_id: str
    prompt_version: str
    rendered_prompt_sha256: str
    response_schema_id: str
    response_schema_version: str


@dataclass(frozen=True, slots=True)
class SubjectLink:
    subject_id: str
    subject_type: str
    provider: str
    connector: str
    connector_version: str
    model_identifier: str
    reported_model_version: str | None = None


@dataclass(slots=True)
class ObservationRecord:
    """Canonical in-memory representation of one observation."""

    observation_id: str
    run_id: str
    condition_id: str
    attempt_id: str
    status: ObservationStatus
    experiment: ExperimentLink
    dataset: DatasetLink
    prompt: PromptLink
    subject: SubjectLink

    observation_schema_version: str = OBSERVATION_SCHEMA_VERSION
    execution: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_dry_run(
        cls,
        *,
        sequence: int,
        run_id: str,
        condition_id: str,
        experiment: ExperimentLink,
        dataset: DatasetLink,
        prompt_id: str,
        prompt_version: str,
        rendered_prompt: str,
        response_schema_id: str,
        response_schema_version: str,
        subject: SubjectLink,
        execution_parameters: Mapping[str, Any] | None = None,
    ) -> "ObservationRecord":
        """Create a planned dry-run observation with no model response."""

        created_at = utc_now_iso()
        prompt_hash = sha256_text(rendered_prompt)

        request_payload = {
            "rendered_prompt": rendered_prompt,
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
        }
        request_hash = sha256_text(canonical_json(request_payload))

        execution = {
            "mode": "dry_run",
            "parameters": dict(execution_parameters or {}),
            "model_call_performed": False,
        }

        configuration_hash = sha256_text(
            canonical_json(
                {
                    "experiment": asdict(experiment),
                    "dataset": asdict(dataset),
                    "prompt_id": prompt_id,
                    "prompt_version": prompt_version,
                    "subject": asdict(subject),
                    "execution": execution,
                }
            )
        )

        return cls(
            observation_id=canonical_observation_id(sequence),
            run_id=run_id,
            condition_id=condition_id,
            attempt_id="ATTEMPT-001",
            status=ObservationStatus.PENDING,
            experiment=experiment,
            dataset=dataset,
            prompt=PromptLink(
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                rendered_prompt_sha256=prompt_hash,
                response_schema_id=response_schema_id,
                response_schema_version=response_schema_version,
            ),
            subject=subject,
            execution=execution,
            timing={
                "created_at_utc": created_at,
                "started_at_utc": None,
                "completed_at_utc": None,
                "latency_seconds": None,
            },
            request={
                "request_sha256": request_hash,
                "rendered_prompt": rendered_prompt,
            },
            response={
                "raw_text": None,
                "response_sha256": None,
                "finish_reason": None,
            },
            integrity={
                "algorithm": "SHA-256",
                "configuration_sha256": configuration_hash,
            },
            cache={
                "was_cached": False,
                "cache_key": None,
                "source_observation_id": None,
            },
            error={
                "category": None,
                "message": None,
                "retryable": False,
            },
            environment={
                "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
                "python_version": platform.python_version(),
                "operating_system": platform.system(),
                "platform": platform.platform(),
            },
            evaluation={
                "state": EvaluationState.NOT_STARTED.value,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible canonical observation dictionary."""

        value = asdict(self)
        value["status"] = self.status.value
        return value

    def to_json(self, *, pretty: bool = True) -> str:
        """Serialize the observation to JSON."""

        if pretty:
            return json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )

        return canonical_json(self.to_dict())

    def write_atomic(self, path: str | Path) -> Path:
        """Write the observation atomically and return the final path."""

        final_path = Path(path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = final_path.with_name(final_path.name + ".tmp")
        payload = self.to_json(pretty=True) + "\n"

        try:
            with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())

            temporary_path.replace(final_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return final_path


__all__ = [
    "DatasetLink",
    "EvaluationState",
    "ExperimentLink",
    "ObservationRecord",
    "ObservationStatus",
    "PromptLink",
    "SubjectLink",
    "canonical_json",
    "canonical_observation_id",
    "sha256_text",
    "utc_now_iso",
]
