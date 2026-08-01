"""Interruption-safe checkpointed batch runner."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Callable

from experiment_manager import ExperimentManager, ExperimentRecord, ExperimentStatus

from .loading import CaseExecutor
from .models import BatchCase, BatchPlan, BatchRunSummary, CaseExecutionResult


ProgressCallback = Callable[[dict[str, object]], None]


class BatchRunner:
    """Execute an ordered plan using the C1 experiment checkpoint."""

    def __init__(
        self,
        manager: ExperimentManager,
        *,
        sleep_function: Callable[[float], None] = time.sleep,
    ) -> None:
        self.manager = manager
        self.sleep_function = sleep_function

    def run(
        self,
        plan: BatchPlan,
        executor: CaseExecutor,
        *,
        dry_run: bool = False,
        max_cases: int | None = None,
        progress: ProgressCallback | None = None,
    ) -> BatchRunSummary:
        if max_cases is not None and max_cases <= 0:
            raise ValueError("max_cases must be positive when supplied.")

        specification = self.manager.load_specification(plan.experiment_id)
        checkpoint = self.manager.load_checkpoint(plan.experiment_id)
        state = self.manager.load_state(plan.experiment_id)

        if specification.case_count != len(plan.cases):
            raise RuntimeError(
                "Batch plan case count does not match experiment specification: "
                f"{len(plan.cases)} != {specification.case_count}."
            )

        if state.status == ExperimentStatus.COMPLETED:
            return BatchRunSummary(
                experiment_id=plan.experiment_id,
                starting_case_number=checkpoint.next_case_number,
                ending_case_number=checkpoint.next_case_number,
                attempted_count=0,
                completed_count=0,
                failed_count=0,
                skipped_count=len(plan.cases),
                interrupted=False,
                dry_run=dry_run,
            )

        starting_case_number = checkpoint.next_case_number
        pending = plan.cases[starting_case_number:]

        if max_cases is not None:
            pending = pending[:max_cases]

        if dry_run:
            self._emit(
                progress,
                event="dry_run",
                experiment_id=plan.experiment_id,
                starting_case_number=starting_case_number,
                scheduled_count=len(pending),
            )
            return BatchRunSummary(
                experiment_id=plan.experiment_id,
                starting_case_number=starting_case_number,
                ending_case_number=starting_case_number,
                attempted_count=0,
                completed_count=0,
                failed_count=0,
                skipped_count=len(plan.cases) - len(pending),
                interrupted=False,
                dry_run=True,
            )

        if state.status != ExperimentStatus.RUNNING:
            self.manager.start(plan.experiment_id)

        attempted_count = 0
        completed_count = 0
        failed_count = 0
        interrupted = False

        for case in pending:
            self._emit(
                progress,
                event="case_started",
                experiment_id=plan.experiment_id,
                case_number=case.case_number,
                case_id=case.case_id,
            )

            try:
                result, attempts = self._execute_with_retry(
                    case,
                    executor,
                    plan,
                    progress,
                )
            except KeyboardInterrupt:
                self.manager.pause(plan.experiment_id)
                interrupted = True
                self._emit(
                    progress,
                    event="interrupted",
                    experiment_id=plan.experiment_id,
                    case_number=case.case_number,
                    case_id=case.case_id,
                )
                break
            except Exception as exc:
                attempted_count += 1
                failed_count += 1
                failed_result = CaseExecutionResult(
                    response_text="",
                    parsed_prediction=None,
                    actual_value=None,
                    is_correct=None,
                    confidence=None,
                    latency_seconds=None,
                    successful=False,
                    metadata={
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "runner_attempts": plan.retry_policy.max_attempts,
                    },
                )
                self._append(plan.experiment_id, case, failed_result)
                self._emit(
                    progress,
                    event="case_failed",
                    experiment_id=plan.experiment_id,
                    case_number=case.case_number,
                    case_id=case.case_id,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
                if plan.stop_on_failure:
                    self.manager.pause(plan.experiment_id)
                    break
                continue

            attempted_count += 1
            if result.successful:
                completed_count += 1
            else:
                failed_count += 1

            result = replace(
                result,
                metadata={
                    **dict(result.metadata),
                    "runner_attempts": attempts,
                },
            )
            self._append(plan.experiment_id, case, result)

            self._emit(
                progress,
                event="case_completed" if result.successful else "case_failed",
                experiment_id=plan.experiment_id,
                case_number=case.case_number,
                case_id=case.case_id,
                attempts=attempts,
            )

            if not result.successful and plan.stop_on_failure:
                self.manager.pause(plan.experiment_id)
                break

        final_checkpoint = self.manager.load_checkpoint(plan.experiment_id)

        if (
            final_checkpoint.next_case_number >= len(plan.cases)
            and final_checkpoint.failed_case_count == 0
        ):
            self.manager.complete(plan.experiment_id)
        elif not interrupted:
            current_state = self.manager.load_state(plan.experiment_id)
            if current_state.status == ExperimentStatus.RUNNING:
                self.manager.pause(plan.experiment_id)

        return BatchRunSummary(
            experiment_id=plan.experiment_id,
            starting_case_number=starting_case_number,
            ending_case_number=final_checkpoint.next_case_number,
            attempted_count=attempted_count,
            completed_count=completed_count,
            failed_count=failed_count,
            skipped_count=starting_case_number,
            interrupted=interrupted,
            dry_run=False,
        )

    def _execute_with_retry(
        self,
        case: BatchCase,
        executor: CaseExecutor,
        plan: BatchPlan,
        progress: ProgressCallback | None,
    ) -> tuple[CaseExecutionResult, int]:
        policy = plan.retry_policy
        last_exception: Exception | None = None
        last_result: CaseExecutionResult | None = None

        for attempt in range(1, policy.max_attempts + 1):
            try:
                result = executor(case)
                if not isinstance(result, CaseExecutionResult):
                    raise TypeError(
                        "Executor must return CaseExecutionResult."
                    )
                last_result = result
                if result.successful or not policy.retry_unsuccessful_results:
                    return result, attempt
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                last_exception = exc
                if not policy.retry_exceptions:
                    raise

            if attempt < policy.max_attempts:
                self._emit(
                    progress,
                    event="case_retry",
                    experiment_id=plan.experiment_id,
                    case_number=case.case_number,
                    case_id=case.case_id,
                    attempt=attempt,
                )
                if policy.delay_seconds:
                    self.sleep_function(policy.delay_seconds)

        if last_exception is not None:
            raise last_exception
        if last_result is not None:
            return last_result, policy.max_attempts
        raise RuntimeError("Executor produced neither a result nor an exception.")

    def _append(
        self,
        experiment_id: str,
        case: BatchCase,
        result: CaseExecutionResult,
    ) -> None:
        record = ExperimentRecord(
            case_id=case.case_id,
            sequence_index=case.sequence_index,
            window_size=case.window_size,
            prompt_sha256=case.prompt_sha256,
            response_text=result.response_text,
            parsed_prediction=result.parsed_prediction,
            actual_value=result.actual_value,
            is_correct=result.is_correct,
            confidence=result.confidence,
            latency_seconds=result.latency_seconds,
            provider_request_id=result.provider_request_id,
            metadata={
                **dict(case.payload),
                **dict(result.metadata),
                "case_number": case.case_number,
            },
        )
        self.manager.append_record(
            experiment_id,
            record,
            successful=result.successful,
        )

    @staticmethod
    def _emit(
        callback: ProgressCallback | None,
        **event: object,
    ) -> None:
        if callback is not None:
            callback(dict(event))
