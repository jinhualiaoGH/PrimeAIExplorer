from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from kernel.exceptions import ValidationError
from model_providers import ProviderResponse

from .execution import EvaluationOutcome


def _mapping(name: str, value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValidationError(f"{name} must be a mapping.")
    return dict(value)


@dataclass(frozen=True, slots=True)
class SemanticEvaluationRequest:
    """Provider-independent input to a semantic evaluator."""

    expected: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _mapping("metadata", self.metadata))


class SemanticEvaluator(Protocol):
    evaluator_id: str

    def evaluate(
        self,
        response: ProviderResponse,
        request: SemanticEvaluationRequest,
    ) -> EvaluationOutcome:
        ...


def parse_json_object(text: str) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None

    stripped = text.strip()

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        value = None

    if isinstance(value, dict):
        return value

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        return None

    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    return value if isinstance(value, dict) else None


def parse_first_integer(text: str) -> int | None:
    if not isinstance(text, str):
        return None

    payload = parse_json_object(text)
    if payload is not None:
        for key in ("prediction", "answer", "value"):
            value = payload.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            if isinstance(value, str):
                token = value.strip()
                if re.fullmatch(r"-?\d+", token):
                    return int(token)

    match = re.search(r"(?<!\d)-?\d+(?!\d)", text)
    return int(match.group()) if match else None


def extract_confidence(text: str) -> int | None:
    payload = parse_json_object(text)
    if payload is None:
        return None

    value = payload.get("confidence")
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100:
        return value
    return None


class ExactIntegerEvaluator:
    evaluator_id = "numeric_exact"

    def evaluate(
        self,
        response: ProviderResponse,
        request: SemanticEvaluationRequest,
    ) -> EvaluationOutcome:
        expected = request.expected
        if isinstance(expected, bool) or not isinstance(expected, int):
            raise ValidationError("numeric_exact expected value must be an integer.")

        observed = parse_first_integer(response.text)

        return EvaluationOutcome(
            passed=observed == expected,
            score=100.0 if observed == expected else 0.0,
            confidence=extract_confidence(response.text),
            surface_answer=response.text,
            semantic_answer=observed,
            metadata={
                "evaluator_id": self.evaluator_id,
                "expected": expected,
                "parsed": observed is not None,
            },
        )


class ExactTextEvaluator:
    evaluator_id = "text_exact"

    def evaluate(
        self,
        response: ProviderResponse,
        request: SemanticEvaluationRequest,
    ) -> EvaluationOutcome:
        if not isinstance(request.expected, str):
            raise ValidationError("text_exact expected value must be text.")

        observed = response.text.strip()
        expected = request.expected.strip()
        passed = observed == expected

        return EvaluationOutcome(
            passed=passed,
            score=100.0 if passed else 0.0,
            confidence=extract_confidence(response.text),
            surface_answer=response.text,
            semantic_answer=observed,
            metadata={
                "evaluator_id": self.evaluator_id,
                "expected": expected,
            },
        )


class StructuredPredictionEvaluator:
    """Evaluate JSON-like prediction payloads semantically.

    Expected input is a mapping. Every expected field must be present and
    semantically equal in the parsed response. Additional response fields are
    allowed. Numeric values are compared numerically.
    """

    evaluator_id = "structured_prediction"

    @staticmethod
    def _equivalent(expected: Any, observed: Any) -> bool:
        if isinstance(expected, bool):
            return observed is expected

        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            if isinstance(observed, bool) or not isinstance(observed, (int, float)):
                return False
            return math.isclose(
                float(expected),
                float(observed),
                rel_tol=0.0,
                abs_tol=1e-12,
            )

        if isinstance(expected, str):
            return isinstance(observed, str) and observed.strip() == expected.strip()

        if expected is None:
            return observed is None

        return observed == expected

    def evaluate(
        self,
        response: ProviderResponse,
        request: SemanticEvaluationRequest,
    ) -> EvaluationOutcome:
        if not isinstance(request.expected, Mapping):
            raise ValidationError(
                "structured_prediction expected value must be a mapping."
            )

        parsed = parse_json_object(response.text)
        if parsed is None:
            return EvaluationOutcome(
                passed=False,
                score=0.0,
                confidence=None,
                surface_answer=response.text,
                semantic_answer=None,
                metadata={
                    "evaluator_id": self.evaluator_id,
                    "parsed": False,
                    "required_fields": sorted(str(key) for key in request.expected),
                },
            )

        field_results: dict[str, bool] = {}
        for key, expected_value in request.expected.items():
            key_text = str(key)
            field_results[key_text] = (
                key in parsed
                and self._equivalent(expected_value, parsed[key])
            )

        matched = sum(field_results.values())
        total = len(field_results)
        score = 100.0 if total == 0 else 100.0 * matched / total
        passed = matched == total

        return EvaluationOutcome(
            passed=passed,
            score=score,
            confidence=extract_confidence(response.text),
            surface_answer=response.text,
            semantic_answer=parsed,
            metadata={
                "evaluator_id": self.evaluator_id,
                "parsed": True,
                "field_results": field_results,
                "matched_fields": matched,
                "required_fields": total,
            },
        )
