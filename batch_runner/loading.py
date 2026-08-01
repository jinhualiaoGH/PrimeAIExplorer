"""Load batch plans and executor callables."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .models import BatchCase, BatchPlan, CaseExecutionResult, RetryPolicy


class CaseExecutor(Protocol):
    def __call__(self, case: BatchCase) -> CaseExecutionResult:
        """Execute one case and return a normalized result."""


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return value


def batch_plan_from_document(document: Mapping[str, Any]) -> BatchPlan:
    raw_retry = dict(document.get("retry_policy", {}))
    retry_policy = RetryPolicy(
        max_attempts=int(raw_retry.get("max_attempts", 1)),
        delay_seconds=float(raw_retry.get("delay_seconds", 0.0)),
        retry_exceptions=bool(raw_retry.get("retry_exceptions", True)),
        retry_unsuccessful_results=bool(
            raw_retry.get("retry_unsuccessful_results", False)
        ),
    )

    cases = tuple(
        BatchCase(
            case_number=int(item["case_number"]),
            case_id=str(item["case_id"]),
            sequence_index=int(item["sequence_index"]),
            window_size=int(item["window_size"]),
            prompt_sha256=str(item["prompt_sha256"]),
            payload=dict(item.get("payload", {})),
        )
        for item in document["cases"]
    )

    return BatchPlan(
        experiment_id=str(document["experiment_id"]),
        cases=cases,
        retry_policy=retry_policy,
        stop_on_failure=bool(document.get("stop_on_failure", False)),
        schema_version=str(document.get("schema_version", "1.0")),
    )


def load_batch_plan(path: str | Path) -> BatchPlan:
    return batch_plan_from_document(load_json_object(Path(path)))


def load_executor(reference: str) -> CaseExecutor:
    """Load an executor from 'package.module:function_name'."""

    module_name, separator, attribute_name = reference.partition(":")
    if not separator or not module_name or not attribute_name:
        raise ValueError(
            "Executor reference must use 'package.module:function_name'."
        )

    module = importlib.import_module(module_name)
    executor = getattr(module, attribute_name)

    if not callable(executor):
        raise TypeError(f"Executor is not callable: {reference}")

    return executor
