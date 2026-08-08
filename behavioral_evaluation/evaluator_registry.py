from __future__ import annotations

from collections.abc import Iterable

from kernel.exceptions import ValidationError

from .evaluators import (
    ExactIntegerEvaluator,
    ExactTextEvaluator,
    SemanticEvaluator,
    StructuredPredictionEvaluator,
)


class SemanticEvaluatorRegistry:
    """Deterministic registry for Phase G4 semantic evaluators."""

    def __init__(self, evaluators: Iterable[SemanticEvaluator] = ()) -> None:
        self._evaluators: dict[str, SemanticEvaluator] = {}
        for evaluator in evaluators:
            self.register(evaluator)

    def register(self, evaluator: SemanticEvaluator) -> None:
        evaluator_id = getattr(evaluator, "evaluator_id", None)
        if not isinstance(evaluator_id, str) or not evaluator_id.strip():
            raise ValidationError("semantic evaluator requires evaluator_id.")

        key = evaluator_id.strip()
        if key in self._evaluators:
            raise ValidationError(
                f"semantic evaluator already registered: {key}"
            )
        self._evaluators[key] = evaluator

    def get(self, evaluator_id: str) -> SemanticEvaluator:
        key = evaluator_id.strip() if isinstance(evaluator_id, str) else ""
        if not key:
            raise ValidationError("evaluator_id must not be empty.")

        try:
            return self._evaluators[key]
        except KeyError as exc:
            raise KeyError(f"unknown semantic evaluator: {key}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._evaluators))


def default_semantic_evaluator_registry() -> SemanticEvaluatorRegistry:
    return SemanticEvaluatorRegistry(
        (
            ExactIntegerEvaluator(),
            ExactTextEvaluator(),
            StructuredPredictionEvaluator(),
        )
    )
