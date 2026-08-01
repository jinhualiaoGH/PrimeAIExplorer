from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
from sequence_api.models import SequenceWindow


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{name} must not be empty.")
    return normalized


def _positive(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer.")
    if value <= 0:
        raise ValidationError(f"{name} must be positive.")
    return value


@dataclass(frozen=True)
class SequenceDatasetSpec:
    schema_version: str
    dataset_id: str
    dataset_version: str
    sequence_id: str
    title: str
    start_index: int
    case_count: int
    observation_count: int
    target_count: int
    stride: int
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        if self.schema_version != "1.0":
            raise ValidationError("unsupported dataset schema version.")
        object.__setattr__(self, "dataset_id", _text("dataset_id", self.dataset_id))
        object.__setattr__(self, "dataset_version", _text("dataset_version", self.dataset_version))
        object.__setattr__(self, "sequence_id", _text("sequence_id", self.sequence_id))
        object.__setattr__(self, "title", _text("title", self.title))
        if isinstance(self.start_index, bool) or not isinstance(self.start_index, int):
            raise ValidationError("start_index must be an integer.")
        _positive("case_count", self.case_count)
        _positive("observation_count", self.observation_count)
        _positive("target_count", self.target_count)
        _positive("stride", self.stride)
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SequenceDatasetSpec":
        if not isinstance(payload, Mapping):
            raise ValidationError("dataset specification must be a mapping.")
        required = {
            "dataset_id",
            "sequence_id",
            "start_index",
            "case_count",
            "observation_count",
            "target_count",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"dataset specification is missing fields: {missing}")
        return cls(
            schema_version=payload.get("schema_version", "1.0"),
            dataset_id=payload["dataset_id"],
            dataset_version=payload.get("dataset_version", "1.0.0"),
            sequence_id=payload["sequence_id"],
            title=payload.get("title", payload["dataset_id"]),
            start_index=payload["start_index"],
            case_count=payload["case_count"],
            observation_count=payload["observation_count"],
            target_count=payload["target_count"],
            stride=payload.get("stride", 1),
            metadata=payload.get("metadata", {}),
        )

    @property
    def values_per_case(self) -> int:
        return self.observation_count + self.target_count

    @property
    def final_case_start_index(self) -> int:
        return self.start_index + (self.case_count - 1) * self.stride

    @property
    def final_required_index(self) -> int:
        return self.final_case_start_index + self.values_per_case - 1

    def case_start_index(self, case_index: int) -> int:
        if isinstance(case_index, bool) or not isinstance(case_index, int):
            raise ValidationError("case_index must be an integer.")
        if case_index < 0 or case_index >= self.case_count:
            raise ValidationError("case_index is outside the dataset.")
        return self.start_index + case_index * self.stride

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "sequence_id": self.sequence_id,
            "title": self.title,
            "start_index": self.start_index,
            "case_count": self.case_count,
            "observation_count": self.observation_count,
            "target_count": self.target_count,
            "stride": self.stride,
            "values_per_case": self.values_per_case,
            "final_case_start_index": self.final_case_start_index,
            "final_required_index": self.final_required_index,
            "metadata": dict(self.metadata),
        }

    @property
    def dataset_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class DatasetCaseRequest:
    dataset_id: str
    case_index: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _text("dataset_id", self.dataset_id))
        if isinstance(self.case_index, bool) or not isinstance(self.case_index, int):
            raise ValidationError("case_index must be an integer.")
        if self.case_index < 0:
            raise ValidationError("case_index must be nonnegative.")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DatasetCaseRequest":
        if not isinstance(payload, Mapping):
            raise ValidationError("dataset case request must be a mapping.")
        required = {"dataset_id", "case_index"}
        missing = sorted(required - set(payload))
        if missing:
            raise ValidationError(f"dataset case request is missing fields: {missing}")
        return cls(payload["dataset_id"], payload["case_index"])

    def to_dict(self) -> dict[str, Any]:
        return {"dataset_id": self.dataset_id, "case_index": self.case_index}

    @property
    def request_sha256(self) -> str:
        return stable_sha256(self.to_dict())


@dataclass(frozen=True)
class DatasetCase:
    schema_version: str
    dataset_id: str
    dataset_sha256: str
    case_index: int
    case_id: str
    sequence_id: str
    start_index: int
    observation: tuple[int | float, ...]
    target: tuple[int | float, ...]
    descriptor_sha256: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        object.__setattr__(self, "dataset_id", _text("dataset_id", self.dataset_id))
        object.__setattr__(self, "case_id", _text("case_id", self.case_id))
        object.__setattr__(self, "sequence_id", _text("sequence_id", self.sequence_id))
        for name, digest in (
            ("dataset_sha256", self.dataset_sha256),
            ("descriptor_sha256", self.descriptor_sha256),
        ):
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValidationError(f"{name} must contain 64 characters.")
        if isinstance(self.case_index, bool) or not isinstance(self.case_index, int):
            raise ValidationError("case_index must be an integer.")
        if self.case_index < 0:
            raise ValidationError("case_index must be nonnegative.")
        if isinstance(self.start_index, bool) or not isinstance(self.start_index, int):
            raise ValidationError("start_index must be an integer.")
        object.__setattr__(self, "observation", tuple(self.observation))
        object.__setattr__(self, "target", tuple(self.target))
        if not self.observation:
            raise ValidationError("observation must not be empty.")
        if not self.target:
            raise ValidationError("target must not be empty.")
        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_window(
        cls,
        spec: SequenceDatasetSpec,
        case_index: int,
        window: SequenceWindow,
    ) -> "DatasetCase":
        if len(window.values) != spec.values_per_case:
            raise ValidationError("sequence window length does not match dataset case.")
        observation = tuple(window.values[: spec.observation_count])
        target = tuple(window.values[spec.observation_count :])
        case_payload = {
            "dataset_sha256": spec.dataset_sha256,
            "case_index": case_index,
            "sequence_id": window.sequence_id,
            "start_index": window.start_index,
            "observation": observation,
            "target": target,
            "descriptor_sha256": window.descriptor_sha256,
        }
        case_hash = stable_sha256(case_payload)
        return cls(
            schema_version="1.0",
            dataset_id=spec.dataset_id,
            dataset_sha256=spec.dataset_sha256,
            case_index=case_index,
            case_id=f"{spec.dataset_id}:{case_index:08d}:{case_hash[:16]}",
            sequence_id=window.sequence_id,
            start_index=window.start_index,
            observation=observation,
            target=target,
            descriptor_sha256=window.descriptor_sha256,
            metadata={
                "observation_count": spec.observation_count,
                "target_count": spec.target_count,
                "stride": spec.stride,
                "case_sha256": case_hash,
            },
        )

    @property
    def target_start_index(self) -> int:
        return self.start_index + len(self.observation)

    @property
    def end_index(self) -> int:
        return self.target_start_index + len(self.target) - 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id,
            "dataset_sha256": self.dataset_sha256,
            "case_index": self.case_index,
            "case_id": self.case_id,
            "sequence_id": self.sequence_id,
            "start_index": self.start_index,
            "target_start_index": self.target_start_index,
            "end_index": self.end_index,
            "observation": list(self.observation),
            "target": list(self.target),
            "descriptor_sha256": self.descriptor_sha256,
            "metadata": dict(self.metadata),
        }

    @property
    def case_sha256(self) -> str:
        return self.metadata["case_sha256"]


@dataclass(frozen=True)
class DatasetCaseBatch:
    cases: tuple[DatasetCase, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))
        if not self.cases:
            raise ValidationError("dataset case batch must not be empty.")
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValidationError("dataset case batch contains duplicate cases.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "cases": [case.to_dict() for case in self.cases],
            "batch_sha256": self.batch_sha256,
        }

    @property
    def batch_sha256(self) -> str:
        return stable_sha256([case.to_dict() for case in self.cases])
