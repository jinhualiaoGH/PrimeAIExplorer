from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .identity import canonical_metadata, sha256_json
from .validation import optional_text, require_positive_int, require_probability, require_text


class FailurePolicy(str, Enum):
    FAIL_FAST = "fail_fast"
    CONTINUE = "continue"


class SeedPolicy(str, Enum):
    NONE = "none"
    FIXED = "fixed"
    DERIVED = "derived"


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    dataset_id: str
    version: str
    split: str = "default"
    selector: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", require_text("dataset_id", self.dataset_id))
        object.__setattr__(self, "version", require_text("version", self.version))
        object.__setattr__(self, "split", require_text("split", self.split))
        if not isinstance(self.selector, Mapping):
            raise ValidationError("selector must be a mapping.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "selector", dict(self.selector))
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "split": self.split,
            "selector": dict(self.selector),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PromptSpec:
    prompt_id: str
    version: str
    system_prompt_id: str | None = None
    template_variables: Mapping[str, Any] = field(default_factory=dict)
    json_mode: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt_id", require_text("prompt_id", self.prompt_id))
        object.__setattr__(self, "version", require_text("version", self.version))
        object.__setattr__(
            self,
            "system_prompt_id",
            optional_text("system_prompt_id", self.system_prompt_id),
        )
        if not isinstance(self.template_variables, Mapping):
            raise ValidationError("template_variables must be a mapping.")
        if not isinstance(self.json_mode, bool):
            raise ValidationError("json_mode must be boolean.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "template_variables", dict(self.template_variables))
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "system_prompt_id": self.system_prompt_id,
            "template_variables": dict(self.template_variables),
            "json_mode": self.json_mode,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProviderTarget:
    provider: str
    model: str
    temperature: float = 0.0
    max_output_tokens: int | None = None
    seed: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", require_text("provider", self.provider))
        object.__setattr__(self, "model", require_text("model", self.model))

        if isinstance(self.temperature, bool) or not isinstance(self.temperature, (int, float)):
            raise ValidationError("temperature must be numeric.")
        temperature = float(self.temperature)
        if temperature < 0.0:
            raise ValidationError("temperature must be non-negative.")
        object.__setattr__(self, "temperature", temperature)

        if self.max_output_tokens is not None:
            object.__setattr__(
                self,
                "max_output_tokens",
                require_positive_int("max_output_tokens", self.max_output_tokens),
            )
        if self.seed is not None and (isinstance(self.seed, bool) or not isinstance(self.seed, int)):
            raise ValidationError("seed must be an integer or None.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def target_id(self) -> str:
        return f"{self.provider}/{self.model}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "seed": self.seed,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class TrialPolicy:
    repetitions: int = 1
    retries_per_trial: int = 0
    timeout_seconds: float | None = None
    failure_policy: FailurePolicy = FailurePolicy.CONTINUE

    def __post_init__(self) -> None:
        object.__setattr__(self, "repetitions", require_positive_int("repetitions", self.repetitions))
        if isinstance(self.retries_per_trial, bool) or not isinstance(self.retries_per_trial, int):
            raise ValidationError("retries_per_trial must be a non-negative integer.")
        if self.retries_per_trial < 0:
            raise ValidationError("retries_per_trial must be a non-negative integer.")

        if self.timeout_seconds is not None:
            if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)):
                raise ValidationError("timeout_seconds must be numeric or None.")
            if float(self.timeout_seconds) <= 0:
                raise ValidationError("timeout_seconds must be positive.")
            object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))

        try:
            object.__setattr__(self, "failure_policy", FailurePolicy(self.failure_policy))
        except ValueError as exc:
            raise ValidationError("failure_policy is invalid.") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "repetitions": self.repetitions,
            "retries_per_trial": self.retries_per_trial,
            "timeout_seconds": self.timeout_seconds,
            "failure_policy": self.failure_policy.value,
        }


@dataclass(frozen=True, slots=True)
class ReproducibilityPolicy:
    seed_policy: SeedPolicy = SeedPolicy.DERIVED
    base_seed: int | None = 0
    require_provider_request_id: bool = False
    capture_raw_response: bool = True
    capture_environment: bool = True

    def __post_init__(self) -> None:
        try:
            policy = SeedPolicy(self.seed_policy)
        except ValueError as exc:
            raise ValidationError("seed_policy is invalid.") from exc
        object.__setattr__(self, "seed_policy", policy)

        if self.base_seed is not None and (
            isinstance(self.base_seed, bool) or not isinstance(self.base_seed, int)
        ):
            raise ValidationError("base_seed must be an integer or None.")
        if policy == SeedPolicy.FIXED and self.base_seed is None:
            raise ValidationError("fixed seed policy requires base_seed.")

        for name in (
            "require_provider_request_id",
            "capture_raw_response",
            "capture_environment",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ValidationError(f"{name} must be boolean.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_policy": self.seed_policy.value,
            "base_seed": self.base_seed,
            "require_provider_request_id": self.require_provider_request_id,
            "capture_raw_response": self.capture_raw_response,
            "capture_environment": self.capture_environment,
        }


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    max_parallel_jobs: int = 1
    randomize_job_order: bool = False
    provider_failure_tolerance: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_parallel_jobs",
            require_positive_int("max_parallel_jobs", self.max_parallel_jobs),
        )
        if not isinstance(self.randomize_job_order, bool):
            raise ValidationError("randomize_job_order must be boolean.")
        object.__setattr__(
            self,
            "provider_failure_tolerance",
            require_probability(
                "provider_failure_tolerance",
                self.provider_failure_tolerance,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_parallel_jobs": self.max_parallel_jobs,
            "randomize_job_order": self.randomize_job_order,
            "provider_failure_tolerance": self.provider_failure_tolerance,
        }


@dataclass(frozen=True, slots=True)
class ExperimentDefinition:
    experiment_id: str
    title: str
    task_family: str
    dataset_spec: DatasetSpec
    prompt_spec: PromptSpec
    evaluation_contract_id: str
    provider_targets: tuple[ProviderTarget, ...]
    trial_policy: TrialPolicy = field(default_factory=TrialPolicy)
    reproducibility_policy: ReproducibilityPolicy = field(default_factory=ReproducibilityPolicy)
    description: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", require_text("experiment_id", self.experiment_id))
        object.__setattr__(self, "title", require_text("title", self.title))
        object.__setattr__(self, "task_family", require_text("task_family", self.task_family))
        object.__setattr__(
            self,
            "evaluation_contract_id",
            require_text("evaluation_contract_id", self.evaluation_contract_id),
        )
        object.__setattr__(self, "description", optional_text("description", self.description))

        if not isinstance(self.dataset_spec, DatasetSpec):
            raise ValidationError("dataset_spec must be DatasetSpec.")
        if not isinstance(self.prompt_spec, PromptSpec):
            raise ValidationError("prompt_spec must be PromptSpec.")
        if not isinstance(self.trial_policy, TrialPolicy):
            raise ValidationError("trial_policy must be TrialPolicy.")
        if not isinstance(self.reproducibility_policy, ReproducibilityPolicy):
            raise ValidationError("reproducibility_policy must be ReproducibilityPolicy.")

        targets = tuple(self.provider_targets)
        if not targets:
            raise ValidationError("provider_targets cannot be empty.")
        for item in targets:
            if not isinstance(item, ProviderTarget):
                raise ValidationError("provider_targets must contain ProviderTarget values.")
        target_ids = tuple(item.target_id for item in targets)
        if len(set(target_ids)) != len(target_ids):
            raise ValidationError("provider_targets contains duplicate targets.")
        object.__setattr__(self, "provider_targets", tuple(sorted(targets, key=lambda item: item.target_id)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h1.0",
            "experiment_id": self.experiment_id,
            "title": self.title,
            "description": self.description,
            "task_family": self.task_family,
            "dataset_spec": self.dataset_spec.to_dict(),
            "prompt_spec": self.prompt_spec.to_dict(),
            "evaluation_contract_id": self.evaluation_contract_id,
            "provider_targets": [item.to_dict() for item in self.provider_targets],
            "trial_policy": self.trial_policy.to_dict(),
            "reproducibility_policy": self.reproducibility_policy.to_dict(),
            "metadata": dict(self.metadata),
        }

    @property
    def experiment_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["experiment_sha256"] = self.experiment_sha256
        return payload


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    campaign_id: str
    title: str
    experiments: tuple[ExperimentDefinition, ...]
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "campaign_id", require_text("campaign_id", self.campaign_id))
        object.__setattr__(self, "title", require_text("title", self.title))

        experiments = tuple(self.experiments)
        if not experiments:
            raise ValidationError("experiments cannot be empty.")
        for item in experiments:
            if not isinstance(item, ExperimentDefinition):
                raise ValidationError("experiments must contain ExperimentDefinition values.")
        experiment_ids = tuple(item.experiment_id for item in experiments)
        if len(set(experiment_ids)) != len(experiment_ids):
            raise ValidationError("experiments contains duplicate experiment IDs.")
        object.__setattr__(
            self,
            "experiments",
            tuple(sorted(experiments, key=lambda item: item.experiment_id)),
        )

        if not isinstance(self.execution_policy, ExecutionPolicy):
            raise ValidationError("execution_policy must be ExecutionPolicy.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def provider_targets(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    target.target_id
                    for experiment in self.experiments
                    for target in experiment.provider_targets
                }
            )
        )

    @property
    def total_planned_trials(self) -> int:
        return sum(
            len(experiment.provider_targets) * experiment.trial_policy.repetitions
            for experiment in self.experiments
        )

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h1.0",
            "campaign_id": self.campaign_id,
            "title": self.title,
            "experiments": [item.to_dict() for item in self.experiments],
            "execution_policy": self.execution_policy.to_dict(),
            "metadata": dict(self.metadata),
        }

    @property
    def campaign_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "campaign_sha256": self.campaign_sha256,
                "provider_targets": list(self.provider_targets),
                "total_planned_trials": self.total_planned_trials,
            }
        )
        return payload
