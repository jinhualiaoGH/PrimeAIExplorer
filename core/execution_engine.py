"""Deterministic end-to-end execution engine for PrimeAIExplorer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Iterable, Sequence

from connectors import (
    ConnectorMessage,
    ConnectorRequest,
    ConnectorStatus,
    DeterministicMockConnector,
    MessageRole,
    MockMode,
    canonical_request_id,
)
from core.evaluation import evaluate_required_json_fields
from core.execution_context import ExecutionContext
from core.observation import (
    DatasetLink,
    ExperimentLink,
    ObservationRecord,
    ObservationStatus,
    PromptLink,
    SubjectLink,
)
from core.registry_loader import RegistryLoader
from core.report import ReportSection, build_experiment_report


EXECUTION_ENGINE_VERSION = "0.8.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def write_text_atomic(
    path: str | Path,
    payload: str,
) -> Path:
    final_path = Path(path)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = final_path.with_name(
        final_path.name + ".tmp"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        temporary_path.replace(final_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return final_path


@dataclass(frozen=True, slots=True)
class ExecutionCase:
    case_id: str
    condition_id: str
    record_id: str
    user_prompt: str
    required_response_fields: tuple[str, ...] = (
        "prediction",
        "confidence",
        "abstain",
    )

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("Case ID cannot be empty.")

        if not self.condition_id:
            raise ValueError("Condition ID cannot be empty.")

        if not self.user_prompt:
            raise ValueError("User prompt cannot be empty.")


class RunEventLog:
    """Append-only JSON Lines execution event log."""

    def __init__(
        self,
        path: str | Path,
        run_id: str,
    ) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self.sequence = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        phase: str,
        status: str,
        message: str,
        duration_seconds: float | None = None,
        artifact: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        self.sequence += 1

        event = {
            "event_sequence": self.sequence,
            "timestamp_utc": utc_now_iso(),
            "run_id": self.run_id,
            "phase": phase,
            "status": status,
            "message": message,
            "duration_seconds": duration_seconds,
            "artifact": artifact,
            "error": error,
        }

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

        return event


class ExecutionEngine:
    """Execute deterministic scientific cases end to end."""

    def __init__(
        self,
        *,
        root: str | Path,
        context: ExecutionContext,
        execution_profile_id: str = "EXEC-000001",
    ) -> None:
        self.root = Path(root).resolve()
        self.context = context
        self.execution_profile_id = execution_profile_id
        self.output_directory = Path(
            context.output_directory
        )
        self.loader = RegistryLoader(self.root)

    def run(
        self,
        cases: Sequence[ExecutionCase],
    ) -> dict[str, Any]:
        if not cases:
            raise ValueError(
                "At least one execution case is required."
            )

        output = self.output_directory
        observations_directory = output / "observations"
        evaluations_directory = output / "evaluations"
        report_directory = output / "report"

        output.mkdir(parents=True, exist_ok=True)
        observations_directory.mkdir(exist_ok=True)
        evaluations_directory.mkdir(exist_ok=True)

        event_log = RunEventLog(
            output / "events.jsonl",
            self.context.run_id,
        )

        created_at = utc_now_iso()
        phases: list[dict[str, Any]] = []
        artifacts: list[dict[str, str]] = []

        accounting = {
            "planned_cases": len(cases),
            "executed_cases": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "valid_evaluations": 0,
            "invalid_evaluations": 0,
            "observations": 0,
            "evaluations": 0,
            "external_access_count": 0,
            "paid_call_count": 0,
            "total_latency_seconds": 0.0,
        }

        def phase(
            name: str,
            operation,
        ):
            started = utc_now_iso()
            clock = time.perf_counter()

            event_log.append(
                phase=name,
                status="started",
                message=f"Phase started: {name}",
            )

            try:
                result = operation()
            except Exception as error:
                duration = time.perf_counter() - clock
                completed = utc_now_iso()

                phases.append(
                    {
                        "phase": name,
                        "status": "failed",
                        "started_at_utc": started,
                        "completed_at_utc": completed,
                        "duration_seconds": duration,
                        "message": str(error),
                    }
                )

                event_log.append(
                    phase=name,
                    status="failed",
                    message=f"Phase failed: {name}",
                    duration_seconds=duration,
                    error=str(error),
                )
                raise

            duration = time.perf_counter() - clock
            completed = utc_now_iso()

            phases.append(
                {
                    "phase": name,
                    "status": "completed",
                    "started_at_utc": started,
                    "completed_at_utc": completed,
                    "duration_seconds": duration,
                    "message": f"Phase completed: {name}",
                }
            )

            event_log.append(
                phase=name,
                status="completed",
                message=f"Phase completed: {name}",
                duration_seconds=duration,
            )

            return result

        selection = phase(
            "validate",
            lambda: self.loader.validate_selection(
                experiment_id=self.context.experiment_id,
                dataset_id=self.context.dataset_id,
                prompt_id=self.context.prompt_id,
                connector_id=self.context.connector_id,
                execution_profile_id=self.execution_profile_id,
                free_mode=True,
            ),
        )

        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION
        )

        observation_ids: list[str] = []
        evaluation_ids: list[str] = []

        def execute_cases() -> None:
            for index, case in enumerate(cases, start=1):
                request = ConnectorRequest(
                    request_id=canonical_request_id(index),
                    connector_id=connector.connector_id,
                    connector_version=connector.connector_version,
                    subject_id=self.context.subject_id,
                    model_identifier=self.context.model_identifier,
                    messages=(
                        ConnectorMessage(
                            role=MessageRole.SYSTEM,
                            content=(
                                "Return a deterministic JSON object "
                                "with prediction, confidence, and abstain."
                            ),
                        ),
                        ConnectorMessage(
                            role=MessageRole.USER,
                            content=case.user_prompt,
                        ),
                    ),
                    parameters={
                        "seed": self.context.random_seed,
                        "case_id": case.case_id,
                    },
                    response_format={
                        "type": "json_object",
                    },
                    timeout_seconds=30.0,
                    metadata={
                        "run_id": self.context.run_id,
                        "case_id": case.case_id,
                        "condition_id": case.condition_id,
                    },
                )

                response = connector.execute(request)
                accounting["executed_cases"] += 1
                accounting["total_latency_seconds"] += (
                    response.timing.latency_seconds
                )

                if response.provider_metadata.get(
                    "external_access"
                ):
                    accounting["external_access_count"] += 1

                if response.provider_metadata.get(
                    "cost_incurred"
                ):
                    accounting["paid_call_count"] += 1

                if response.status is ConnectorStatus.SUCCEEDED:
                    accounting["successful_responses"] += 1
                    observation_status = ObservationStatus.SUCCEEDED
                else:
                    accounting["failed_responses"] += 1
                    observation_status = ObservationStatus.FAILED

                observation_id = f"OBS-{index:010d}"
                observation_ids.append(observation_id)

                observation = ObservationRecord(
                    observation_id=observation_id,
                    run_id=self.context.run_id,
                    condition_id=case.condition_id,
                    attempt_id="ATTEMPT-001",
                    status=observation_status,
                    experiment=ExperimentLink(
                        experiment_id=self.context.experiment_id,
                        experiment_version=(
                            self.context.experiment_version
                        ),
                        experimental_universe="PrimeNet",
                        hypothesis_id=None,
                    ),
                    dataset=DatasetLink(
                        dataset_id=self.context.dataset_id,
                        dataset_version=self.context.dataset_version,
                        partition="calibration",
                        record_id=case.record_id,
                        artifact_sha256=None,
                    ),
                    prompt=PromptLink(
                        prompt_id=self.context.prompt_id,
                        prompt_version=self.context.prompt_version,
                        rendered_prompt_sha256=sha256_text(
                            case.user_prompt
                        ),
                        response_schema_id="RESPONSE-000001",
                        response_schema_version="0.1.0",
                    ),
                    subject=SubjectLink(
                        subject_id=self.context.subject_id,
                        subject_type="deterministic_baseline",
                        provider="PrimeAIExplorer",
                        connector=connector.connector_id,
                        connector_version=(
                            connector.connector_version
                        ),
                        model_identifier=(
                            self.context.model_identifier
                        ),
                        reported_model_version="0.1.0",
                    ),
                    execution={
                        "mode": "local",
                        "parameters": dict(request.parameters),
                        "connector_status": response.status.value,
                    },
                    timing={
                        "created_at_utc": (
                            response.timing.started_at_utc
                        ),
                        "started_at_utc": (
                            response.timing.started_at_utc
                        ),
                        "completed_at_utc": (
                            response.timing.completed_at_utc
                        ),
                        "latency_seconds": (
                            response.timing.latency_seconds
                        ),
                    },
                    request={
                        "request_sha256": response.request_sha256,
                        "rendered_prompt": case.user_prompt,
                    },
                    response={
                        "raw_text": response.raw_text,
                        "response_sha256": (
                            response.response_sha256
                        ),
                        "finish_reason": response.finish_reason,
                        "provider_metadata": dict(
                            response.provider_metadata
                        ),
                        "usage": response.usage.to_dict(),
                    },
                    integrity={
                        "algorithm": "SHA-256",
                        "configuration_sha256": sha256_text(
                            canonical_json(
                                {
                                    "context": (
                                        self.context.to_dict()
                                    ),
                                    "case_id": case.case_id,
                                    "request_sha256": (
                                        response.request_sha256
                                    ),
                                }
                            )
                        ),
                    },
                    cache={
                        "was_cached": False,
                        "cache_key": None,
                        "source_observation_id": None,
                    },
                    error={
                        "category": response.error.category,
                        "message": response.error.message,
                        "retryable": response.error.retryable,
                    },
                    environment={
                        "primeaiexplorer_version": "0.8.0",
                        "python_version": (
                            platform.python_version()
                        ),
                        "operating_system": platform.system(),
                    },
                    evaluation={
                        "state": "pending",
                    },
                )

                observation_path = (
                    observations_directory
                    / f"{observation_id}.json"
                )
                observation.write_atomic(observation_path)
                accounting["observations"] += 1

                event_log.append(
                    phase="preserve_observations",
                    status="completed",
                    message=(
                        f"Observation preserved: "
                        f"{observation_id}"
                    ),
                    artifact=str(
                        observation_path.relative_to(output)
                    ),
                )

                evaluation_sequence = index
                evaluation = evaluate_required_json_fields(
                    sequence=evaluation_sequence,
                    observation_id=observation_id,
                    observation_schema_version="0.3.0",
                    response_sha256=response.response_sha256,
                    raw_text=response.raw_text or "",
                    required_fields=(
                        case.required_response_fields
                    ),
                )

                evaluation_id = (
                    evaluation.evaluation_result_id
                )
                evaluation_ids.append(evaluation_id)

                evaluation_path = (
                    evaluations_directory
                    / f"{evaluation_id}.json"
                )
                evaluation.write_atomic(evaluation_path)
                accounting["evaluations"] += 1

                if evaluation.validity["is_valid"]:
                    accounting["valid_evaluations"] += 1
                else:
                    accounting["invalid_evaluations"] += 1

                event_log.append(
                    phase="evaluate",
                    status="completed",
                    message=(
                        f"Evaluation preserved: "
                        f"{evaluation_id}"
                    ),
                    artifact=str(
                        evaluation_path.relative_to(output)
                    ),
                )

        phase("execute", execute_cases)

        run_statistics = {
            "run_id": self.context.run_id,
            "summary_type": "descriptive_run_accounting",
            "generated_at_utc": utc_now_iso(),
            "accounting": dict(accounting),
            "scientific_note": (
                "This run used a deterministic mock connector. "
                "It is pipeline-validation evidence, not "
                "frontier-model evidence."
            ),
        }

        run_statistics_path = output / "run_statistics.json"

        phase(
            "summarize",
            lambda: write_text_atomic(
                run_statistics_path,
                json.dumps(
                    run_statistics,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
            ),
        )

        report = phase(
            "report",
            lambda: build_experiment_report(
                sequence=1,
                title=(
                    "PrimeAIExplorer v0.8 Deterministic "
                    "Execution Report"
                ),
                authors=["Jinhua Liao"],
                experiment_id=self.context.experiment_id,
                experiment_version=(
                    self.context.experiment_version
                ),
                sections=[
                    ReportSection(
                        section_id="scope",
                        title="Scientific Scope",
                        content=(
                            "This run validates the complete local "
                            "PrimeAIExplorer execution pipeline."
                        ),
                    ),
                    ReportSection(
                        section_id="protocol",
                        title="Execution Protocol",
                        content=(
                            "All cases were executed through "
                            "CONNECTOR-000001, the deterministic "
                            "mock connector. No external access or "
                            "paid model call occurred."
                        ),
                    ),
                    ReportSection(
                        section_id="results",
                        title="Results",
                        content=(
                            f"Planned cases: "
                            f"{accounting['planned_cases']}\n\n"
                            f"Executed cases: "
                            f"{accounting['executed_cases']}\n\n"
                            f"Valid evaluations: "
                            f"{accounting['valid_evaluations']}\n\n"
                            f"Invalid evaluations: "
                            f"{accounting['invalid_evaluations']}"
                        ),
                    ),
                    ReportSection(
                        section_id="limitations",
                        title="Limitations",
                        content=(
                            "The deterministic mock connector is "
                            "not a language model. These results "
                            "validate infrastructure only and must "
                            "not be interpreted as evidence about "
                            "foundation-model intelligence."
                        ),
                    ),
                ],
                observation_ids=observation_ids,
                evaluation_result_ids=evaluation_ids,
                statistical_summary_ids=[],
            ),
        )

        report_paths = report.write_atomic(report_directory)

        artifact_paths = [
            output / "events.jsonl",
            run_statistics_path,
            *sorted(observations_directory.glob("*.json")),
            *sorted(evaluations_directory.glob("*.json")),
            report_paths["markdown"],
            report_paths["manifest"],
        ]

        for artifact_path in artifact_paths:
            relative = artifact_path.relative_to(output)

            if relative.name == "events.jsonl":
                artifact_type = "event_log"
            elif relative.name == "run_statistics.json":
                artifact_type = "run_statistics"
            elif "observations" in relative.parts:
                artifact_type = "observation"
            elif "evaluations" in relative.parts:
                artifact_type = "evaluation"
            elif relative.name.endswith(".md"):
                artifact_type = "scientific_report"
            else:
                artifact_type = "report_manifest"

            artifacts.append(
                {
                    "artifact_type": artifact_type,
                    "relative_path": relative.as_posix(),
                    "sha256": sha256(
                        artifact_path.read_bytes()
                    ).hexdigest(),
                }
            )

        final_status = (
            "completed"
            if (
                accounting["failed_responses"] == 0
                and accounting["invalid_evaluations"] == 0
            )
            else "completed_with_failures"
        )

        completed_at = utc_now_iso()

        manifest_without_hash = {
            "run_id": self.context.run_id,
            "run_schema_version": "0.8.0",
            "status": final_status,
            "context": self.context.to_dict(),
            "selection": selection,
            "phases": phases,
            "accounting": accounting,
            "artifacts": artifacts,
            "environment": {
                "primeaiexplorer_version": "0.8.0",
                "execution_engine_version": (
                    EXECUTION_ENGINE_VERSION
                ),
                "python_version": platform.python_version(),
                "operating_system": platform.system(),
                "platform": platform.platform(),
            },
            "created_at_utc": created_at,
            "completed_at_utc": completed_at,
        }

        manifest_hash = sha256_text(
            canonical_json(manifest_without_hash)
        )

        manifest = {
            **manifest_without_hash,
            "integrity": {
                "algorithm": "SHA-256",
                "manifest_sha256": manifest_hash,
            },
        }

        manifest_path = output / "run_manifest.json"

        write_text_atomic(
            manifest_path,
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )

        event_log.append(
            phase="finalize",
            status="completed",
            message=(
                f"Run finalized with status: {final_status}"
            ),
            artifact="run_manifest.json",
        )

        return manifest


__all__ = [
    "ExecutionCase",
    "ExecutionEngine",
    "RunEventLog",
    "canonical_json",
    "sha256_text",
    "utc_now_iso",
    "write_text_atomic",
]
