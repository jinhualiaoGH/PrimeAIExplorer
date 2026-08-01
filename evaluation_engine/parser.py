from __future__ import annotations

import json
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from evaluation_engine.models import ParsedPrediction


_REQUIRED_FIELDS = {"prediction", "confidence", "explanation"}


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def parse_prediction_response(response_text: str) -> ParsedPrediction:
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValidationError("response_text must not be empty.")

    candidate = _strip_code_fence(response_text)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"response_text is not valid JSON: {exc.msg}"
        ) from exc

    if not isinstance(payload, Mapping):
        raise ValidationError("response JSON must be an object.")

    missing = sorted(_REQUIRED_FIELDS - set(payload))
    extra = sorted(set(payload) - _REQUIRED_FIELDS)
    if missing:
        raise ValidationError(f"response JSON is missing fields: {missing}")
    if extra:
        raise ValidationError(f"response JSON contains unexpected fields: {extra}")

    prediction = payload["prediction"]
    confidence = payload["confidence"]
    explanation = payload["explanation"]

    if isinstance(prediction, bool) or not isinstance(prediction, (int, float)):
        raise ValidationError("prediction must be numeric.")
    if isinstance(confidence, bool) or not isinstance(confidence, int):
        raise ValidationError("confidence must be an integer.")
    if not 0 <= confidence <= 100:
        raise ValidationError("confidence must be from 0 to 100.")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValidationError("explanation must be nonempty text.")

    return ParsedPrediction(
        prediction=prediction,
        confidence=confidence,
        explanation=explanation,
        raw_payload=payload,
    )
