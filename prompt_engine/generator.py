from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

from kernel.context import ExecutionContext
from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
from prompt_engine.models import (
    GeneratedPrompt,
    PromptBatch,
    PromptRequest,
)
from prompt_engine.registry import PromptTemplateRegistry
from sequence_api.dataset_engine import SequenceDatasetEngine
from sequence_api.dataset_models import DatasetCaseRequest


def _format_values(values: tuple[int | float, ...]) -> str:
    return " ".join(str(value) for value in values)


def _response_schema_text(schema: dict[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True)


@dataclass
class DeterministicPromptGenerator:
    datasets: SequenceDatasetEngine
    templates: PromptTemplateRegistry

    def generate(
        self,
        request: PromptRequest,
        context: ExecutionContext,
    ) -> GeneratedPrompt:
        template = self.templates.resolve(request.template_id)
        case = self.datasets.case(
            DatasetCaseRequest(request.dataset_id, request.case_index),
            context,
        )

        replacements = {
            "dataset_id": case.dataset_id,
            "case_id": case.case_id,
            "case_index": str(case.case_index),
            "sequence_id": case.sequence_id,
            "start_index": str(case.start_index),
            "target_start_index": str(case.target_start_index),
            "end_index": str(case.end_index),
            "observation_count": str(len(case.observation)),
            "target_count": str(len(case.target)),
            "observed_values": _format_values(case.observation),
            "response_schema": _response_schema_text(dict(template.response_schema)),
        }

        try:
            system_message = template.system_template.format(**replacements)
            user_message = template.user_template.format(**replacements)
        except KeyError as exc:
            raise ValidationError(
                f"prompt template contains an unsupported placeholder: {exc.args[0]!r}"
            ) from exc

        identity_payload = {
            "template_sha256": template.template_sha256,
            "dataset_sha256": case.dataset_sha256,
            "case_sha256": case.case_sha256,
            "system_message": system_message,
            "user_message": user_message,
            "response_schema": dict(template.response_schema),
        }
        prompt_sha256 = stable_sha256(identity_payload)
        prompt_id = (
            f"{template.template_id}:{case.dataset_id}:"
            f"{case.case_index:08d}:{prompt_sha256[:16]}"
        )

        return GeneratedPrompt(
            schema_version="1.0",
            prompt_id=prompt_id,
            prompt_sha256=prompt_sha256,
            template_id=template.template_id,
            template_sha256=template.template_sha256,
            dataset_id=case.dataset_id,
            dataset_sha256=case.dataset_sha256,
            case_id=case.case_id,
            case_sha256=case.case_sha256,
            case_index=case.case_index,
            system_message=system_message,
            user_message=user_message,
            response_schema=template.response_schema,
            ground_truth=case.target if request.include_ground_truth else None,
            metadata={
                "sequence_id": case.sequence_id,
                "observation_count": len(case.observation),
                "target_count": len(case.target),
                "start_index": case.start_index,
                "target_start_index": case.target_start_index,
                "end_index": case.end_index,
                "ground_truth_included": request.include_ground_truth,
            },
        )

    def batch(
        self,
        requests: Sequence[PromptRequest],
        context: ExecutionContext,
    ) -> PromptBatch:
        if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)):
            raise ValidationError("prompt batch requests must be a sequence.")
        return PromptBatch(
            tuple(self.generate(request, context) for request in requests)
        )
