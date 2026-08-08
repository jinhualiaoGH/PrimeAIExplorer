from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError

from .contracts import ExperimentDefinition, ProviderTarget, SeedPolicy
from .identity import canonical_metadata, sha256_json
from .prompts import PromptTemplate
from .suite_registry import ResolvedInputSuite
from .validation import require_text


@dataclass(frozen=True, slots=True)
class SourceRecord:
    record_id: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", require_text("record_id", self.record_id))
        if not isinstance(self.payload, Mapping):
            raise ValidationError("payload must be a mapping.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    @property
    def record_sha256(self) -> str:
        return sha256_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class MaterializedCase:
    case_id: str
    experiment_id: str
    experiment_sha256: str
    input_suite_sha256: str
    dataset_id: str
    dataset_version: str
    dataset_split: str
    dataset_descriptor_sha256: str
    source_record_id: str
    source_record_sha256: str
    prompt_id: str
    prompt_version: str
    prompt_sha256: str
    prompt_text: str
    system_prompt: str | None
    provider: str
    model: str
    target_id: str
    repetition_index: int
    seed: int | None
    json_mode: bool
    temperature: float
    max_output_tokens: int | None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "case_id",
            "experiment_id",
            "experiment_sha256",
            "input_suite_sha256",
            "dataset_id",
            "dataset_version",
            "dataset_split",
            "dataset_descriptor_sha256",
            "source_record_id",
            "source_record_sha256",
            "prompt_id",
            "prompt_version",
            "prompt_sha256",
            "prompt_text",
            "provider",
            "model",
            "target_id",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if self.system_prompt is not None:
            object.__setattr__(
                self,
                "system_prompt",
                require_text("system_prompt", self.system_prompt),
            )

        if (
            isinstance(self.repetition_index, bool)
            or not isinstance(self.repetition_index, int)
            or self.repetition_index <= 0
        ):
            raise ValidationError("repetition_index must be a positive integer.")

        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValidationError("seed must be an integer or None.")

        if not isinstance(self.json_mode, bool):
            raise ValidationError("json_mode must be boolean.")

        if isinstance(self.temperature, bool) or not isinstance(
            self.temperature, (int, float)
        ):
            raise ValidationError("temperature must be numeric.")
        temperature = float(self.temperature)
        if temperature < 0:
            raise ValidationError("temperature must be non-negative.")
        object.__setattr__(self, "temperature", temperature)

        if self.max_output_tokens is not None:
            if (
                isinstance(self.max_output_tokens, bool)
                or not isinstance(self.max_output_tokens, int)
                or self.max_output_tokens <= 0
            ):
                raise ValidationError(
                    "max_output_tokens must be a positive integer or None."
                )

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h3.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "input_suite_sha256": self.input_suite_sha256,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "dataset_split": self.dataset_split,
            "dataset_descriptor_sha256": self.dataset_descriptor_sha256,
            "source_record_id": self.source_record_id,
            "source_record_sha256": self.source_record_sha256,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "prompt_sha256": self.prompt_sha256,
            "prompt_text": self.prompt_text,
            "system_prompt": self.system_prompt,
            "provider": self.provider,
            "model": self.model,
            "target_id": self.target_id,
            "repetition_index": self.repetition_index,
            "seed": self.seed,
            "json_mode": self.json_mode,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "metadata": dict(self.metadata),
        }

    @property
    def case_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["case_id"] = self.case_id
        payload["case_sha256"] = self.case_sha256
        return payload


@dataclass(frozen=True, slots=True)
class ExperimentMaterialization:
    experiment_id: str
    experiment_sha256: str
    input_suite_sha256: str
    cases: tuple[MaterializedCase, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", require_text("experiment_id", self.experiment_id))
        object.__setattr__(
            self,
            "experiment_sha256",
            require_text("experiment_sha256", self.experiment_sha256),
        )
        object.__setattr__(
            self,
            "input_suite_sha256",
            require_text("input_suite_sha256", self.input_suite_sha256),
        )

        cases = tuple(self.cases)
        for case in cases:
            if not isinstance(case, MaterializedCase):
                raise ValidationError("cases must contain MaterializedCase values.")
            if case.experiment_id != self.experiment_id:
                raise ValidationError("case experiment_id mismatch.")
            if case.experiment_sha256 != self.experiment_sha256:
                raise ValidationError("case experiment_sha256 mismatch.")
            if case.input_suite_sha256 != self.input_suite_sha256:
                raise ValidationError("case input_suite_sha256 mismatch.")

        case_ids = tuple(case.case_id for case in cases)
        if len(set(case_ids)) != len(case_ids):
            raise ValidationError("materialization contains duplicate case IDs.")

        object.__setattr__(self, "cases", tuple(sorted(cases, key=lambda case: case.case_id)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def case_count(self) -> int:
        return len(self.cases)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "h3.0",
            "experiment_id": self.experiment_id,
            "experiment_sha256": self.experiment_sha256,
            "input_suite_sha256": self.input_suite_sha256,
            "case_sha256s": [case.case_sha256 for case in self.cases],
            "metadata": dict(self.metadata),
        }

    @property
    def materialization_sha256(self) -> str:
        return sha256_json(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload.update(
            {
                "materialization_sha256": self.materialization_sha256,
                "case_count": self.case_count,
                "cases": [case.to_dict() for case in self.cases],
            }
        )
        return payload


class ExperimentMaterializer:
    def materialize(
        self,
        *,
        experiment: ExperimentDefinition,
        inputs: ResolvedInputSuite,
        records: Iterable[SourceRecord | Mapping[str, Any]],
        metadata: Mapping[str, Any] | None = None,
    ) -> ExperimentMaterialization:
        if not isinstance(experiment, ExperimentDefinition):
            raise ValidationError("experiment must be ExperimentDefinition.")
        if not isinstance(inputs, ResolvedInputSuite):
            raise ValidationError("inputs must be ResolvedInputSuite.")

        self._validate_input_contract(experiment, inputs)

        source_records = tuple(self._coerce_record(value) for value in records)
        record_ids = tuple(record.record_id for record in source_records)
        if len(set(record_ids)) != len(record_ids):
            raise ValidationError("records contains duplicate record IDs.")

        prompt = self._resolve_prompt(experiment, inputs)
        cases: list[MaterializedCase] = []

        for record in sorted(source_records, key=lambda item: item.record_id):
            variables = dict(experiment.prompt_spec.template_variables)
            variables.update(record.payload)
            prompt_text = prompt.render(variables)

            for target in experiment.provider_targets:
                for repetition_index in range(
                    1,
                    experiment.trial_policy.repetitions + 1,
                ):
                    seed = self._resolve_seed(
                        experiment=experiment,
                        target=target,
                        record=record,
                        repetition_index=repetition_index,
                    )
                    case_id = self._case_id(
                        experiment=experiment,
                        inputs=inputs,
                        prompt=prompt,
                        target=target,
                        record=record,
                        repetition_index=repetition_index,
                        seed=seed,
                    )

                    cases.append(
                        MaterializedCase(
                            case_id=case_id,
                            experiment_id=experiment.experiment_id,
                            experiment_sha256=experiment.experiment_sha256,
                            input_suite_sha256=inputs.suite_sha256,
                            dataset_id=inputs.dataset.dataset_id,
                            dataset_version=inputs.dataset.version,
                            dataset_split=inputs.dataset.split,
                            dataset_descriptor_sha256=inputs.dataset.descriptor_sha256,
                            source_record_id=record.record_id,
                            source_record_sha256=record.record_sha256,
                            prompt_id=prompt.prompt_id,
                            prompt_version=prompt.version,
                            prompt_sha256=prompt.prompt_sha256,
                            prompt_text=prompt_text,
                            system_prompt=prompt.system_prompt,
                            provider=target.provider,
                            model=target.model,
                            target_id=target.target_id,
                            repetition_index=repetition_index,
                            seed=seed,
                            json_mode=prompt.json_mode,
                            temperature=target.temperature,
                            max_output_tokens=target.max_output_tokens,
                            metadata={
                                "evaluation_contract_id": experiment.evaluation_contract_id,
                                "task_family": experiment.task_family,
                                "source_record_metadata": dict(record.metadata),
                            },
                        )
                    )

        return ExperimentMaterialization(
            experiment_id=experiment.experiment_id,
            experiment_sha256=experiment.experiment_sha256,
            input_suite_sha256=inputs.suite_sha256,
            cases=tuple(cases),
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _coerce_record(value: SourceRecord | Mapping[str, Any]) -> SourceRecord:
        if isinstance(value, SourceRecord):
            return value
        if not isinstance(value, Mapping):
            raise ValidationError("records must contain SourceRecord or mapping values.")

        raw = dict(value)
        if "record_id" not in raw:
            raise ValidationError("record mapping requires record_id.")

        record_id = raw.pop("record_id")
        metadata = raw.pop("metadata", {})
        payload = raw.pop("payload", raw)

        if raw and "payload" in value:
            raise ValidationError(
                "record mappings using payload may contain only record_id, payload, and metadata."
            )

        return SourceRecord(
            record_id=record_id,
            payload=payload,
            metadata=metadata,
        )

    @staticmethod
    def _resolve_prompt(
        experiment: ExperimentDefinition,
        inputs: ResolvedInputSuite,
    ) -> PromptTemplate:
        matches = tuple(
            prompt
            for prompt in inputs.prompts
            if prompt.prompt_id == experiment.prompt_spec.prompt_id
            and prompt.version == experiment.prompt_spec.version
        )
        if len(matches) != 1:
            raise ValidationError(
                "resolved input suite must contain exactly one prompt matching "
                "experiment.prompt_spec."
            )
        return matches[0]

    @staticmethod
    def _validate_input_contract(
        experiment: ExperimentDefinition,
        inputs: ResolvedInputSuite,
    ) -> None:
        dataset_spec = experiment.dataset_spec
        dataset = inputs.dataset

        if (
            dataset_spec.dataset_id != dataset.dataset_id
            or dataset_spec.version != dataset.version
            or dataset_spec.split != dataset.split
        ):
            raise ValidationError(
                "resolved dataset does not match experiment.dataset_spec."
            )

    @staticmethod
    def _resolve_seed(
        *,
        experiment: ExperimentDefinition,
        target: ProviderTarget,
        record: SourceRecord,
        repetition_index: int,
    ) -> int | None:
        if target.seed is not None:
            return target.seed

        policy = experiment.reproducibility_policy
        if policy.seed_policy == SeedPolicy.NONE:
            return None

        if policy.seed_policy == SeedPolicy.FIXED:
            return policy.base_seed

        material = {
            "experiment_sha256": experiment.experiment_sha256,
            "target_id": target.target_id,
            "record_id": record.record_id,
            "record_sha256": record.record_sha256,
            "repetition_index": repetition_index,
            "base_seed": policy.base_seed,
        }
        digest = hashlib.sha256(
            sha256_json(material).encode("utf-8")
        ).hexdigest()
        return int(digest[:16], 16) % (2**31)

    @staticmethod
    def _case_id(
        *,
        experiment: ExperimentDefinition,
        inputs: ResolvedInputSuite,
        prompt: PromptTemplate,
        target: ProviderTarget,
        record: SourceRecord,
        repetition_index: int,
        seed: int | None,
    ) -> str:
        digest = sha256_json(
            {
                "schema_version": "h3.0",
                "experiment_sha256": experiment.experiment_sha256,
                "input_suite_sha256": inputs.suite_sha256,
                "dataset_descriptor_sha256": inputs.dataset.descriptor_sha256,
                "record_id": record.record_id,
                "record_sha256": record.record_sha256,
                "prompt_sha256": prompt.prompt_sha256,
                "target": target.to_dict(),
                "repetition_index": repetition_index,
                "seed": seed,
            }
        )
        return f"{experiment.experiment_id}-CASE-{digest[:16].upper()}"
