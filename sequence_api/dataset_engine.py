from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from sequence_api.dataset_models import (
    DatasetCase,
    DatasetCaseBatch,
    DatasetCaseRequest,
    SequenceDatasetSpec,
)
from sequence_api.models import SequenceWindowRequest
from sequence_api.registry import SequenceProviderRegistry


@dataclass
class SequenceDatasetRegistry:
    _datasets: dict[str, SequenceDatasetSpec] = field(default_factory=dict)

    def register(self, spec: SequenceDatasetSpec) -> None:
        if spec.dataset_id in self._datasets:
            raise ValidationError(f"dataset is already registered: {spec.dataset_id}")
        self._datasets[spec.dataset_id] = spec

    def resolve(self, dataset_id: str) -> SequenceDatasetSpec:
        try:
            return self._datasets[dataset_id]
        except KeyError as exc:
            raise ValidationError(f"unknown dataset_id: {dataset_id!r}") from exc

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._datasets))


@dataclass
class SequenceDatasetEngine:
    providers: SequenceProviderRegistry
    datasets: SequenceDatasetRegistry

    def validate_spec(
        self,
        spec: SequenceDatasetSpec,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        provider = self.providers.resolve(spec.sequence_id)
        descriptor = provider.describe(context)
        if spec.start_index < descriptor.index_origin:
            raise ValidationError("dataset begins before sequence index origin.")
        if descriptor.finite:
            assert descriptor.length is not None
            sequence_end = descriptor.index_origin + descriptor.length - 1
            if spec.final_required_index > sequence_end:
                raise ValidationError("dataset exceeds finite sequence boundary.")
        return {
            "schema_version": "1.0",
            "dataset": spec.to_dict(),
            "dataset_sha256": spec.dataset_sha256,
            "sequence_descriptor_sha256": descriptor.descriptor_sha256,
            "sequence_value_type": descriptor.value_type.value,
            "validated": True,
        }

    def describe(
        self,
        dataset_id: str,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        spec = self.datasets.resolve(dataset_id)
        return self.validate_spec(spec, context)

    def case(
        self,
        request: DatasetCaseRequest,
        context: ExecutionContext,
    ) -> DatasetCase:
        spec = self.datasets.resolve(request.dataset_id)
        self.validate_spec(spec, context)
        provider = self.providers.resolve(spec.sequence_id)
        start_index = spec.case_start_index(request.case_index)
        window = provider.read_window(
            SequenceWindowRequest(
                sequence_id=spec.sequence_id,
                start_index=start_index,
                count=spec.values_per_case,
            ),
            context,
        )
        return DatasetCase.from_window(spec, request.case_index, window)

    def batch(
        self,
        requests: Sequence[DatasetCaseRequest],
        context: ExecutionContext,
    ) -> DatasetCaseBatch:
        if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)):
            raise ValidationError("dataset batch requests must be a sequence.")
        return DatasetCaseBatch(
            tuple(self.case(request, context) for request in requests)
        )
