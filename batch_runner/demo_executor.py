"""Deterministic executor used for Phase C2 smoke testing."""

from __future__ import annotations

import json
import time

from .models import BatchCase, CaseExecutionResult


def execute(case: BatchCase) -> CaseExecutionResult:
    started = time.perf_counter()
    prediction = int(case.payload.get("prediction", 6))
    actual = int(case.payload.get("actual_value", prediction))
    confidence = int(case.payload.get("confidence", 25))

    response = {
        "prediction": prediction,
        "confidence": confidence,
        "explanation": "Deterministic Phase C2 demo executor.",
    }

    return CaseExecutionResult(
        response_text=json.dumps(response, sort_keys=True),
        parsed_prediction=prediction,
        actual_value=actual,
        is_correct=prediction == actual,
        confidence=confidence,
        latency_seconds=time.perf_counter() - started,
        successful=True,
        provider_request_id=None,
        metadata={"executor": "batch_runner.demo_executor:execute"},
    )
