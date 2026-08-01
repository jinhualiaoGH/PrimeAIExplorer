from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from sequence_api.dataset_engine import (
    SequenceDatasetEngine,
    SequenceDatasetRegistry,
)
from sequence_api.dataset_models import (
    DatasetCaseRequest,
    SequenceDatasetSpec,
)
from sequence_api.gap_provider import PartitionedGapSequenceProvider
from sequence_api.memmap_provider import NpyMemmapSequenceProvider
from sequence_api.models import (
    SequenceBatch,
    SequenceBatchRequest,
    SequenceWindowRequest,
)
from sequence_api.primenet_adapter import PrimeNetGapRepositoryAdapter
from sequence_api.providers import InMemorySequenceProvider
from sequence_api.registry import SequenceProviderRegistry


@dataclass
class SequenceExecutionPlugin:
    configuration: Mapping[str, Any] | None = None

    plugin_id = "sequence_api"

    def __post_init__(self) -> None:
        configuration = dict(self.configuration or {})
        self.registry = SequenceProviderRegistry()
        for provider_configuration in configuration.get("providers", ()):
            provider_type = provider_configuration.get("provider_type", "in_memory")
            if provider_type == "in_memory":
                provider = InMemorySequenceProvider.from_configuration(
                    provider_configuration
                )
            elif provider_type == "numpy_npy_memmap":
                provider = NpyMemmapSequenceProvider.from_configuration(
                    provider_configuration
                )
            elif provider_type == "partitioned_gap_uint16":
                provider = PartitionedGapSequenceProvider.from_configuration(
                    provider_configuration
                )
            elif provider_type == "primenet_gap_repository":
                provider = PrimeNetGapRepositoryAdapter.from_configuration(
                    provider_configuration
                )
            else:
                raise ValidationError(
                    f"Unsupported provider_type: {provider_type!r}"
                )
            self.registry.register(provider)

        self.dataset_registry = SequenceDatasetRegistry()
        for dataset_configuration in configuration.get("datasets", ()):
            self.dataset_registry.register(
                SequenceDatasetSpec.from_mapping(dataset_configuration)
            )
        self.dataset_engine = SequenceDatasetEngine(
            providers=self.registry,
            datasets=self.dataset_registry,
        )

        # Lazy import preserves independent importability of prompt_engine and
        # sequence_api while keeping the execution plugin as their integration
        # boundary.
        from prompt_engine import (
            DeterministicPromptGenerator,
            PromptTemplateRegistry,
            PromptTemplateSpec,
        )

        self.prompt_template_registry = PromptTemplateRegistry()
        for template_configuration in configuration.get("prompt_templates", ()):
            self.prompt_template_registry.register(
                PromptTemplateSpec.from_mapping(template_configuration)
            )
        self.prompt_generator = DeterministicPromptGenerator(
            datasets=self.dataset_engine,
            templates=self.prompt_template_registry,
        )

    def health_check(self, context: ExecutionContext) -> bool:
        return bool(context.session_id.strip())

    def close(self) -> None:
        for sequence_id in self.registry.registered_ids():
            closer = getattr(self.registry.resolve(sequence_id), "close", None)
            if closer is not None:
                closer()

    def execute(self, payload: Any, context: ExecutionContext) -> Any:
        if not isinstance(payload, Mapping):
            raise ValidationError("Sequence API payload must be a mapping.")
        operation = payload.get("operation")
        if operation == "describe":
            provider = self.registry.resolve(payload["sequence_id"])
            return provider.describe(context).to_dict()
        if operation == "window":
            request = SequenceWindowRequest.from_mapping(payload)
            provider = self.registry.resolve(request.sequence_id)
            return provider.read_window(request, context).to_dict()
        if operation == "batch":
            raw_requests = payload.get("requests")
            if not isinstance(raw_requests, list):
                raise ValidationError("Batch payload must contain a requests list.")
            request = SequenceBatchRequest(
                tuple(SequenceWindowRequest.from_mapping(item) for item in raw_requests)
            )
            windows = tuple(
                self.registry.resolve(item.sequence_id).read_window(item, context)
                for item in request.requests
            )
            return SequenceBatch(windows).to_dict()
        if operation == "list":
            return {
                "schema_version": "1.0",
                "sequence_ids": list(self.registry.registered_ids()),
            }
        if operation == "dataset.list":
            return {
                "schema_version": "1.0",
                "dataset_ids": list(self.dataset_registry.registered_ids()),
            }
        if operation == "dataset.describe":
            dataset_id = payload.get("dataset_id")
            if not isinstance(dataset_id, str):
                raise ValidationError("dataset.describe requires dataset_id.")
            return self.dataset_engine.describe(dataset_id, context)
        if operation == "dataset.case":
            request = DatasetCaseRequest.from_mapping(payload)
            return self.dataset_engine.case(request, context).to_dict()
        if operation == "dataset.batch":
            raw_requests = payload.get("requests")
            if not isinstance(raw_requests, list):
                raise ValidationError(
                    "dataset.batch payload must contain a requests list."
                )
            requests = tuple(
                DatasetCaseRequest.from_mapping(item) for item in raw_requests
            )
            return self.dataset_engine.batch(requests, context).to_dict()
        if operation == "prompt.template.list":
            return {
                "schema_version": "1.0",
                "template_ids": list(
                    self.prompt_template_registry.registered_ids()
                ),
            }
        if operation == "prompt.template.describe":
            template_id = payload.get("template_id")
            if not isinstance(template_id, str):
                raise ValidationError(
                    "prompt.template.describe requires template_id."
                )
            template = self.prompt_template_registry.resolve(template_id)
            result = template.to_dict()
            result["template_sha256"] = template.template_sha256
            return result
        if operation == "prompt.generate":
            from prompt_engine import PromptRequest

            request = PromptRequest.from_mapping(payload)
            return self.prompt_generator.generate(request, context).to_dict()
        if operation == "prompt.batch":
            raw_requests = payload.get("requests")
            if not isinstance(raw_requests, list):
                raise ValidationError(
                    "prompt.batch payload must contain a requests list."
                )
            from prompt_engine import PromptRequest

            requests = tuple(
                PromptRequest.from_mapping(item) for item in raw_requests
            )
            return self.prompt_generator.batch(requests, context).to_dict()

        if operation == "response.parse":
            from evaluation_engine import parse_prediction_response

            response_text = payload.get("response_text")
            return parse_prediction_response(response_text).to_dict()
        if operation == "response.evaluate":
            from evaluation_engine import RawModelResponse, ResponseEvaluationEngine
            from prompt_engine import PromptRequest

            prompt_request = PromptRequest(
                dataset_id=payload["dataset_id"],
                case_index=payload["case_index"],
                template_id=payload["template_id"],
                include_ground_truth=True,
            )
            prompt = self.prompt_generator.generate(prompt_request, context)
            response = RawModelResponse.from_mapping(payload)
            return ResponseEvaluationEngine().evaluate(prompt, response).to_dict()
        if operation == "response.evaluate_batch":
            from evaluation_engine import RawModelResponse, ResponseEvaluationEngine
            from prompt_engine import PromptRequest

            raw_items = payload.get("items")
            if not isinstance(raw_items, list):
                raise ValidationError(
                    "response.evaluate_batch payload must contain an items list."
                )
            prompts = []
            responses = []
            for item in raw_items:
                if not isinstance(item, Mapping):
                    raise ValidationError("response batch item must be a mapping.")
                prompt_request = PromptRequest(
                    dataset_id=item["dataset_id"],
                    case_index=item["case_index"],
                    template_id=item["template_id"],
                    include_ground_truth=True,
                )
                prompts.append(self.prompt_generator.generate(prompt_request, context))
                responses.append(RawModelResponse.from_mapping(item))
            return ResponseEvaluationEngine().evaluate_batch(
                tuple(prompts),
                tuple(responses),
            ).to_dict()
        raise ValidationError(f"Unsupported sequence operation: {operation!r}")
