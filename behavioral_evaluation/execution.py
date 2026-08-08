from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
from model_providers import ModelProvider, ModelRequest, ProviderResponse

from .contracts import (
    BehavioralEvaluationRecord,
    EvaluationDisposition,
    ProviderExecutionStatus,
)
from .observations import ObservationLedger
from .trials import TrialSpec


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise ValidationError(f"{name} must not be empty.")
    return value


@dataclass(frozen=True, slots=True)
class BehavioralRequestSpec:
    """Provider-neutral request material attached to one G2 trial."""

    prompt: str
    system_prompt: str | None = None
    temperature: float | None = 0.0
    max_output_tokens: int | None = None
    seed: int | None = None
    json_mode: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt", _text("prompt", self.prompt))
        if self.system_prompt is not None:
            object.__setattr__(
                self,
                "system_prompt",
                _text("system_prompt", self.system_prompt),
            )
        if self.max_output_tokens is not None:
            if (
                isinstance(self.max_output_tokens, bool)
                or not isinstance(self.max_output_tokens, int)
                or self.max_output_tokens <= 0
            ):
                raise ValidationError(
                    "max_output_tokens must be a positive integer."
                )
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValidationError("seed must be an integer.")
        if not isinstance(self.json_mode, bool):
            raise ValidationError("json_mode must be boolean.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(self.metadata))

    def build_request(self, trial: TrialSpec) -> ModelRequest:
        if not isinstance(trial, TrialSpec):
            raise ValidationError("trial must be TrialSpec.")
        metadata = {
            "run_id": trial.run_id,
            "case_id": trial.case_id,
            "trial_index": trial.trial_index,
            "contract_id": trial.contract_id,
            "observation_id": trial.observation_id,
            **dict(self.metadata),
        }
        return ModelRequest(
            prompt=self.prompt,
            model=trial.model,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            seed=self.seed,
            json_mode=self.json_mode,
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class EvaluationOutcome:
    """Evaluation result supplied to G3 by an evaluator policy.

    G3 owns provider execution, but not task-specific semantic evaluation.
    A caller-provided outcome builder converts ProviderResponse into this
    provider-neutral value.
    """

    passed: bool
    score: float
    confidence: int | None = None
    surface_answer: Any = None
    semantic_answer: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise ValidationError("passed must be boolean.")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValidationError("score must be numeric.")
        if not 0.0 <= float(self.score) <= 100.0:
            raise ValidationError("score must be from 0 to 100.")
        if self.confidence is not None and (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, int)
            or not 0 <= self.confidence <= 100
        ):
            raise ValidationError("confidence must be an integer from 0 to 100.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(self.metadata))


OutcomeBuilder = Callable[[ProviderResponse], EvaluationOutcome]


def classify_provider_error(exc: BaseException) -> str:
    """Return a stable broad execution-error category."""

    name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    combined = f"{name} {text}"

    if "timeout" in combined or "timed out" in combined:
        return "timeout"
    if (
        "auth" in combined
        or "unauthorized" in combined
        or "forbidden" in combined
        or "401" in combined
        or "403" in combined
    ):
        return "authentication"
    if "rate" in combined and "limit" in combined or "429" in combined:
        return "rate_limit"
    if (
        "balance" in combined
        or "billing" in combined
        or "payment" in combined
        or "402" in combined
    ):
        return "billing"
    if "connection" in combined or "network" in combined:
        return "network"
    return "provider_exception"


class BehavioralProviderExecutionBridge:
    """Connect the Phase F2 ModelProvider interface to G1/G2 observations.

    The bridge invokes exactly one provider call for exactly one TrialSpec.
    It never invents semantic evaluation policy: successful responses are
    scored only through the supplied OutcomeBuilder.
    """

    def __init__(
        self,
        provider: ModelProvider,
        outcome_builder: OutcomeBuilder,
    ) -> None:
        if provider is None:
            raise ValidationError("provider must not be None.")
        if not callable(outcome_builder):
            raise ValidationError("outcome_builder must be callable.")
        self.provider = provider
        self.outcome_builder = outcome_builder

    def execute(
        self,
        trial: TrialSpec,
        request_spec: BehavioralRequestSpec,
    ) -> BehavioralEvaluationRecord:
        if not isinstance(trial, TrialSpec):
            raise ValidationError("trial must be TrialSpec.")
        if not isinstance(request_spec, BehavioralRequestSpec):
            raise ValidationError("request_spec must be BehavioralRequestSpec.")

        request = request_spec.build_request(trial)

        try:
            response = self.provider.generate(request)
        except Exception as exc:
            return BehavioralEvaluationRecord(
                observation_id=trial.observation_id,
                contract_id=trial.contract_id,
                case_id=trial.case_id,
                trial_index=trial.trial_index,
                provider=trial.provider,
                model=trial.model,
                execution_status=ProviderExecutionStatus.PROVIDER_ERROR,
                evaluation_disposition=EvaluationDisposition.NOT_EVALUATED,
                provider_error_category=classify_provider_error(exc),
                provider_error_message=str(exc) or exc.__class__.__name__,
                metadata={
                    "run_id": trial.run_id,
                    "exception_type": exc.__class__.__name__,
                },
            )

        self._validate_response_identity(trial, response)
        outcome = self.outcome_builder(response)

        if not isinstance(outcome, EvaluationOutcome):
            raise ValidationError(
                "outcome_builder must return EvaluationOutcome."
            )

        usage = response.usage
        return BehavioralEvaluationRecord(
            observation_id=trial.observation_id,
            contract_id=trial.contract_id,
            case_id=trial.case_id,
            trial_index=trial.trial_index,
            provider=trial.provider,
            model=trial.model,
            execution_status=ProviderExecutionStatus.COMPLETED,
            evaluation_disposition=EvaluationDisposition.EVALUATED,
            response_sha256=stable_sha256({"text": response.text}),
            passed=outcome.passed,
            score=outcome.score,
            confidence=outcome.confidence,
            latency_seconds=response.latency_seconds,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            surface_answer=outcome.surface_answer,
            semantic_answer=outcome.semantic_answer,
            metadata={
                "run_id": trial.run_id,
                "provider_request_id": response.request_id,
                "finish_reason": response.finish_reason,
                "provider_metadata": dict(response.metadata),
                "evaluation_metadata": dict(outcome.metadata),
            },
        )

    def execute_into(
        self,
        ledger: ObservationLedger,
        trial: TrialSpec,
        request_spec: BehavioralRequestSpec,
    ) -> ObservationLedger:
        if not isinstance(ledger, ObservationLedger):
            raise ValidationError("ledger must be ObservationLedger.")
        if trial.observation_id not in {
            item.observation_id for item in ledger.missing_trials()
        }:
            raise ValidationError(
                "trial is not currently missing from the ledger."
            )
        return ledger.with_record(self.execute(trial, request_spec))

    @staticmethod
    def _validate_response_identity(
        trial: TrialSpec,
        response: ProviderResponse,
    ) -> None:
        if not isinstance(response, ProviderResponse):
            raise ValidationError(
                "provider.generate() must return ProviderResponse."
            )
        if response.provider.strip().lower() != trial.provider.strip().lower():
            raise ValidationError(
                "ProviderResponse.provider does not match TrialSpec.provider."
            )
        if response.model != trial.model:
            raise ValidationError(
                "ProviderResponse.model does not match TrialSpec.model."
            )
