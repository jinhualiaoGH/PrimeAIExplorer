from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from execution.dispatcher import PluginDispatcher
from execution.metrics import ExecutionMetrics
from execution.models import ExecutionRecord, ExecutionRequest
from execution.scheduler import ExecutionScheduler
from kernel.exceptions import RunnerError, ValidationError
from kernel.serialization import stable_sha256
from runtime.lifecycle import RuntimeState
from runtime.session import RuntimeSession


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


@dataclass
class ExecutionEngine:
    session: RuntimeSession
    dispatcher: PluginDispatcher = field(default_factory=PluginDispatcher)
    scheduler: ExecutionScheduler = field(default_factory=ExecutionScheduler)
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    _records: list[ExecutionRecord] = field(default_factory=list)
    _outputs: dict[str, Any] = field(default_factory=dict)

    def submit(self, request: ExecutionRequest) -> None:
        if request.session_id != self.session.context.session_id:
            raise ValidationError(
                "ExecutionRequest session_id does not match RuntimeSession."
            )
        self.scheduler.submit(request)
        self.metrics.record_submission()

    def execute_next(self) -> ExecutionRecord:
        if self.session.state is not RuntimeState.RUNNING:
            raise ValidationError(
                "RuntimeSession must be RUNNING before execution."
            )

        request = self.scheduler.next_request()
        plugin = self.dispatcher.resolve(request.plugin_id)
        started_utc = utc_now()
        started = perf_counter()

        try:
            output = plugin.execute(
                request.payload,
                self.session.context,
            )
        except Exception as exc:
            finished = perf_counter()
            record = ExecutionRecord(
                schema_version="1.0",
                execution_id=request.execution_id,
                plugin_id=request.plugin_id,
                session_id=request.session_id,
                started_utc=started_utc,
                finished_utc=utc_now(),
                elapsed_seconds=finished - started,
                success=False,
                request_sha256=request.request_sha256,
                output_sha256=None,
                error_type=type(exc).__name__,
                error_message=str(exc) or type(exc).__name__,
            )
            self._records.append(record)
            self.metrics.record_completion(record)
            raise RunnerError(
                f"Execution failed: {request.execution_id}"
            ) from exc

        finished = perf_counter()
        output_hash = stable_sha256(output)
        record = ExecutionRecord(
            schema_version="1.0",
            execution_id=request.execution_id,
            plugin_id=request.plugin_id,
            session_id=request.session_id,
            started_utc=started_utc,
            finished_utc=utc_now(),
            elapsed_seconds=finished - started,
            success=True,
            request_sha256=request.request_sha256,
            output_sha256=output_hash,
            error_type=None,
            error_message=None,
        )
        self._outputs[request.execution_id] = output
        self._records.append(record)
        self.metrics.record_completion(record)
        return record

    def execute_all(self) -> tuple[ExecutionRecord, ...]:
        completed = []
        while self.scheduler.pending_count() > 0:
            completed.append(self.execute_next())
        return tuple(completed)

    def output(self, execution_id: str) -> Any:
        if execution_id not in self._outputs:
            raise ValidationError(
                f"No successful output exists for execution: {execution_id}"
            )
        return self._outputs[execution_id]

    def records(self) -> tuple[ExecutionRecord, ...]:
        return tuple(self._records)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "session_id": self.session.context.session_id,
            "registered_plugins": list(self.dispatcher.registered_ids()),
            "pending_execution_ids": list(self.scheduler.pending_ids()),
            "record_hashes": [
                record.record_sha256 for record in self._records
            ],
            "metrics": self.metrics.to_dict(),
        }

    @property
    def snapshot_sha256(self) -> str:
        return stable_sha256(self.snapshot())
