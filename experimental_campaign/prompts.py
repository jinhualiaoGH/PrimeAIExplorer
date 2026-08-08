from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from kernel.exceptions import ValidationError

from .contracts import PromptSpec
from .identity import canonical_metadata
from .suite_identity import registry_entry_identity
from .validation import require_text


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    prompt_id: str
    version: str
    template: str
    system_prompt: str | None = None
    json_mode: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompt_id", require_text("prompt_id", self.prompt_id))
        object.__setattr__(self, "version", require_text("version", self.version))
        object.__setattr__(self, "template", require_text("template", self.template))

        if self.system_prompt is not None:
            object.__setattr__(
                self,
                "system_prompt",
                require_text("system_prompt", self.system_prompt),
            )
        if not isinstance(self.json_mode, bool):
            raise ValidationError("json_mode must be boolean.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def key(self) -> tuple[str, str]:
        return (self.prompt_id, self.version)

    @property
    def registry_id(self) -> str:
        return f"{self.prompt_id}@{self.version}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template": self.template,
            "system_prompt": self.system_prompt,
            "json_mode": self.json_mode,
            "metadata": dict(self.metadata),
        }

    @property
    def prompt_sha256(self) -> str:
        return registry_entry_identity(
            kind="prompt",
            entry_id=self.prompt_id,
            version=self.version,
            payload=self.identity_payload(),
        )

    def render(self, variables: Mapping[str, Any] | None = None) -> str:
        values = dict(variables or {})
        try:
            return self.template.format_map(values)
        except KeyError as exc:
            raise ValidationError(
                f"missing prompt template variable: {exc.args[0]}"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["prompt_sha256"] = self.prompt_sha256
        return payload

    def to_prompt_spec(
        self,
        *,
        template_variables: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> PromptSpec:
        merged_metadata = dict(self.metadata)
        merged_metadata.update(dict(metadata or {}))
        merged_metadata["prompt_sha256"] = self.prompt_sha256

        return PromptSpec(
            prompt_id=self.prompt_id,
            version=self.version,
            system_prompt_id=None,
            template_variables=dict(template_variables or {}),
            json_mode=self.json_mode,
            metadata=merged_metadata,
        )


@dataclass(frozen=True, slots=True)
class PromptSuite:
    suite_id: str
    version: str
    prompt_refs: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "suite_id", require_text("suite_id", self.suite_id))
        object.__setattr__(self, "version", require_text("version", self.version))

        refs = tuple(require_text("prompt_ref", value) for value in self.prompt_refs)
        if not refs:
            raise ValidationError("prompt_refs cannot be empty.")
        if len(set(refs)) != len(refs):
            raise ValidationError("prompt_refs contains duplicate references.")
        object.__setattr__(self, "prompt_refs", tuple(sorted(refs)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @property
    def registry_id(self) -> str:
        return f"{self.suite_id}@{self.version}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "version": self.version,
            "prompt_refs": list(self.prompt_refs),
            "metadata": dict(self.metadata),
        }

    @property
    def suite_sha256(self) -> str:
        return registry_entry_identity(
            kind="prompt_suite",
            entry_id=self.suite_id,
            version=self.version,
            payload=self.identity_payload(),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["suite_sha256"] = self.suite_sha256
        return payload


class PromptRegistry:
    def __init__(
        self,
        prompts: Iterable[PromptTemplate] = (),
        suites: Iterable[PromptSuite] = (),
    ) -> None:
        self._prompts: dict[tuple[str, str], PromptTemplate] = {}
        self._suites: dict[tuple[str, str], PromptSuite] = {}
        for prompt in prompts:
            self.register_prompt(prompt)
        for suite in suites:
            self.register_suite(suite)

    def register_prompt(self, prompt: PromptTemplate) -> PromptTemplate:
        if not isinstance(prompt, PromptTemplate):
            raise ValidationError("prompt must be PromptTemplate.")
        existing = self._prompts.get(prompt.key)
        if existing is None:
            self._prompts[prompt.key] = prompt
            return prompt
        if existing == prompt:
            return existing
        raise ValidationError(f"prompt registry conflict for {prompt.registry_id}.")

    def register_suite(self, suite: PromptSuite) -> PromptSuite:
        if not isinstance(suite, PromptSuite):
            raise ValidationError("suite must be PromptSuite.")
        key = (suite.suite_id, suite.version)
        existing = self._suites.get(key)
        if existing is None:
            self._suites[key] = suite
            return suite
        if existing == suite:
            return existing
        raise ValidationError(f"prompt suite registry conflict for {suite.registry_id}.")

    def get_prompt(self, prompt_id: str, version: str) -> PromptTemplate:
        key = (require_text("prompt_id", prompt_id), require_text("version", version))
        try:
            return self._prompts[key]
        except KeyError as exc:
            raise KeyError(f"prompt not registered: {prompt_id}@{version}") from exc

    def get_suite(self, suite_id: str, version: str) -> PromptSuite:
        key = (require_text("suite_id", suite_id), require_text("version", version))
        try:
            return self._suites[key]
        except KeyError as exc:
            raise KeyError(f"prompt suite not registered: {suite_id}@{version}") from exc

    def prompt_items(self) -> tuple[PromptTemplate, ...]:
        return tuple(self._prompts[key] for key in sorted(self._prompts))

    def suite_items(self) -> tuple[PromptSuite, ...]:
        return tuple(self._suites[key] for key in sorted(self._suites))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h2.0",
            "prompts": [item.to_dict() for item in self.prompt_items()],
            "suites": [item.to_dict() for item in self.suite_items()],
        }
