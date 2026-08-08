from __future__ import annotations

from typing import Any, Callable, Mapping

from kernel.exceptions import ValidationError
from model_providers import ProviderResponse

from .contracts import BehavioralEvaluationContract
from .evaluator_registry import (
    SemanticEvaluatorRegistry,
    default_semantic_evaluator_registry,
)
from .evaluators import SemanticEvaluationRequest
from .execution import EvaluationOutcome


class SemanticEvaluatorRouter:
    """Route a provider response using a G1 contract evaluator_id."""

    def __init__(
        self,
        registry: SemanticEvaluatorRegistry | None = None,
    ) -> None:
        self.registry = registry or default_semantic_evaluator_registry()

    def evaluate(
        self,
        *,
        contract: BehavioralEvaluationContract,
        response: ProviderResponse,
        expected: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvaluationOutcome:
        if not isinstance(contract, BehavioralEvaluationContract):
            raise ValidationError(
                "contract must be BehavioralEvaluationContract."
            )
        if not isinstance(response, ProviderResponse):
            raise ValidationError("response must be ProviderResponse.")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")

        evaluator = self.registry.get(contract.evaluator_id)
        outcome = evaluator.evaluate(
            response,
            SemanticEvaluationRequest(
                expected=expected,
                metadata=dict(metadata or {}),
            ),
        )

        if not isinstance(outcome, EvaluationOutcome):
            raise ValidationError(
                "semantic evaluator must return EvaluationOutcome."
            )

        merged_metadata = {
            **dict(outcome.metadata),
            "contract_id": contract.contract_id,
            "contract_version": contract.contract_version,
            "contract_sha256": contract.contract_sha256,
        }

        return EvaluationOutcome(
            passed=outcome.passed,
            score=outcome.score,
            confidence=outcome.confidence,
            surface_answer=outcome.surface_answer,
            semantic_answer=outcome.semantic_answer,
            metadata=merged_metadata,
        )

    def outcome_builder(
        self,
        *,
        contract: BehavioralEvaluationContract,
        expected: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> Callable[[ProviderResponse], EvaluationOutcome]:
        """Return a G3-compatible OutcomeBuilder."""

        if not isinstance(contract, BehavioralEvaluationContract):
            raise ValidationError(
                "contract must be BehavioralEvaluationContract."
            )
        frozen_metadata = dict(metadata or {})

        def build(response: ProviderResponse) -> EvaluationOutcome:
            return self.evaluate(
                contract=contract,
                response=response,
                expected=expected,
                metadata=frozen_metadata,
            )

        return build
