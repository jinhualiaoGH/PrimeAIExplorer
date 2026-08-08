from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from kernel.exceptions import ValidationError

from .contracts import DatasetSpec, PromptSpec
from .datasets import DatasetDescriptor, DatasetRegistry
from .identity import sha256_json
from .prompts import PromptRegistry, PromptSuite, PromptTemplate


@dataclass(frozen=True, slots=True)
class ResolvedInputSuite:
    dataset: DatasetDescriptor
    prompts: tuple[PromptTemplate, ...]
    dataset_spec: DatasetSpec
    prompt_specs: tuple[PromptSpec, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h2.0",
            "dataset": self.dataset.to_dict(),
            "prompts": [item.to_dict() for item in self.prompts],
            "dataset_spec": self.dataset_spec.to_dict(),
            "prompt_specs": [item.to_dict() for item in self.prompt_specs],
        }

    @property
    def suite_sha256(self) -> str:
        return sha256_json(self.to_dict())


class ExperimentalInputRegistry:
    def __init__(
        self,
        *,
        datasets: DatasetRegistry | None = None,
        prompts: PromptRegistry | None = None,
    ) -> None:
        self.datasets = datasets or DatasetRegistry()
        self.prompts = prompts or PromptRegistry()

    def register_dataset(self, descriptor: DatasetDescriptor) -> DatasetDescriptor:
        return self.datasets.register(descriptor)

    def register_prompt(self, prompt: PromptTemplate) -> PromptTemplate:
        return self.prompts.register_prompt(prompt)

    def register_prompt_suite(self, suite: PromptSuite) -> PromptSuite:
        return self.prompts.register_suite(suite)

    def resolve(
        self,
        *,
        dataset_id: str,
        dataset_version: str,
        dataset_split: str = "default",
        prompt_suite_id: str,
        prompt_suite_version: str,
        dataset_selector: dict[str, Any] | None = None,
    ) -> ResolvedInputSuite:
        dataset = self.datasets.get(dataset_id, dataset_version, dataset_split)
        suite = self.prompts.get_suite(prompt_suite_id, prompt_suite_version)

        prompts: list[PromptTemplate] = []
        for ref in suite.prompt_refs:
            if "@" not in ref:
                raise ValidationError(
                    f"invalid prompt reference in suite {suite.registry_id}: {ref}"
                )
            prompt_id, version = ref.rsplit("@", 1)
            prompts.append(self.prompts.get_prompt(prompt_id, version))

        resolved_prompts = tuple(sorted(prompts, key=lambda item: item.registry_id))
        return ResolvedInputSuite(
            dataset=dataset,
            prompts=resolved_prompts,
            dataset_spec=dataset.to_dataset_spec(selector=dataset_selector),
            prompt_specs=tuple(
                prompt.to_prompt_spec()
                for prompt in resolved_prompts
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h2.0",
            "datasets": self.datasets.to_dict(),
            "prompts": self.prompts.to_dict(),
        }

    @property
    def registry_sha256(self) -> str:
        return sha256_json(self.to_dict())
