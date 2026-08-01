from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{name} must not be empty.")
    return normalized


@dataclass(frozen=True)
class PromptTemplateSpec:
    schema_version: str
    template_id: str
    template_version: str
    title: str
    system_template: str
    user_template: str
    response_schema: Mapping[str, Any]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        if self.schema_version != "1.0":
            raise ValidationError("unsupported prompt-template schema version.")
        object.__setattr__(self, "template_id", _text("template_id", self.template_id))
        object.__setattr__(self, "template_version", _text("template_version", self.template_version))
        object.__setattr__(self, "title", _text("title", self.title))
        object.__setattr__(self, "system_template", _text("system_template", self.system_template))
        object.__setattr__(self, "user_template", _text("user_template", self.user_template))
        if not isinstance(self.response_schema, Mapping):
            raise ValidationError("response_schema must be a mapping.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "response_schema", dict(self.response_schema))
        object.__setattr__(self, "metadata", dict(self.metadata))

        required_tokens = {"{observation_count}", "{observed_values}"}
        missing = sorted(token for token in required_tokens if token not in self.user_template)
        if missing:
            raise ValidationError(
                f"user_template is missing required placeholders: {missing}"
            )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PromptTemplateSpec":
        if not isinstance(payload, Mapping):
            raise ValidationError("prompt template must be a mapping.")
        required = {"template_id", "system_template", "user_template", "response_schema"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"prompt template is missing fields: {missing}")
        return cls(
            schema_version=payload.get("schema_version", "1.0"),
            template_id=payload["template_id"],
            template_version=payload.get("template_version", "1.0.0"),
            title=payload.get("title", payload["template_id"]),
            system_template=payload["system_template"],
            user_template=payload["user_template"],
            response_schema=payload["response_schema"],
            metadata=payload.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "title": self.title,
            "system_template": self.system_template,
            "user_template": self.user_template,
            "response_schema": dict(self.response_schema),
            "metadata": dict(self.metadata),
        }

    @property
    def template_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class PromptRequest:
    dataset_id: str
    case_index: int
    template_id: str
    include_ground_truth: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _text("dataset_id", self.dataset_id))
        object.__setattr__(self, "template_id", _text("template_id", self.template_id))
        if isinstance(self.case_index, bool) or not isinstance(self.case_index, int):
            raise ValidationError("case_index must be an integer.")
        if self.case_index < 0:
            raise ValidationError("case_index must be nonnegative.")
        if not isinstance(self.include_ground_truth, bool):
            raise ValidationError("include_ground_truth must be boolean.")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PromptRequest":
        if not isinstance(payload, Mapping):
            raise ValidationError("prompt request must be a mapping.")
        required = {"dataset_id", "case_index", "template_id"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"prompt request is missing fields: {missing}")
        return cls(
            dataset_id=payload["dataset_id"],
            case_index=payload["case_index"],
            template_id=payload["template_id"],
            include_ground_truth=payload.get("include_ground_truth", False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "case_index": self.case_index,
            "template_id": self.template_id,
            "include_ground_truth": self.include_ground_truth,
        }

    @property
    def request_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class GeneratedPrompt:
    schema_version: str
    prompt_id: str
    prompt_sha256: str
    template_id: str
    template_sha256: str
    dataset_id: str
    dataset_sha256: str
    case_id: str
    case_sha256: str
    case_index: int
    system_message: str
    user_message: str
    response_schema: Mapping[str, Any]
    ground_truth: tuple[int | float, ...] | None
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "prompt_id",
            "template_id",
            "dataset_id",
            "case_id",
            "system_message",
            "user_message",
        ):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        for name in (
            "prompt_sha256",
            "template_sha256",
            "dataset_sha256",
            "case_sha256",
        ):
            digest = getattr(self, name)
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValidationError(f"{name} must contain 64 characters.")
        if isinstance(self.case_index, bool) or not isinstance(self.case_index, int):
            raise ValidationError("case_index must be an integer.")
        if not isinstance(self.response_schema, Mapping):
            raise ValidationError("response_schema must be a mapping.")
        if self.ground_truth is not None:
            object.__setattr__(self, "ground_truth", tuple(self.ground_truth))
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "response_schema", dict(self.response_schema))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "prompt_id": self.prompt_id,
            "prompt_sha256": self.prompt_sha256,
            "template_id": self.template_id,
            "template_sha256": self.template_sha256,
            "dataset_id": self.dataset_id,
            "dataset_sha256": self.dataset_sha256,
            "case_id": self.case_id,
            "case_sha256": self.case_sha256,
            "case_index": self.case_index,
            "system_message": self.system_message,
            "user_message": self.user_message,
            "response_schema": dict(self.response_schema),
            "metadata": dict(self.metadata),
        }
        if self.ground_truth is not None:
            payload["ground_truth"] = list(self.ground_truth)
        return payload


@dataclass(frozen=True)
class PromptBatch:
    prompts: tuple[GeneratedPrompt, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "prompts", tuple(self.prompts))
        if not self.prompts:
            raise ValidationError("prompt batch must not be empty.")
        prompt_ids = [prompt.prompt_id for prompt in self.prompts]
        if len(prompt_ids) != len(set(prompt_ids)):
            raise ValidationError("prompt batch contains duplicate prompts.")

    @property
    def batch_sha256(self) -> str:
        return stable_sha256([prompt.to_dict() for prompt in self.prompts])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "prompts": [prompt.to_dict() for prompt in self.prompts],
            "batch_sha256": self.batch_sha256,
        }
