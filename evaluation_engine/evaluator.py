from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
from prompt_engine.models import GeneratedPrompt
from evaluation_engine.models import (
    EvaluationBatch,
    EvaluationRecord,
    RawModelResponse,
)
from evaluation_engine.parser import parse_prediction_response


@dataclass
class ResponseEvaluationEngine:
    def evaluate(
        self,
        prompt: GeneratedPrompt,
        response: RawModelResponse,
    ) -> EvaluationRecord:
        if response.prompt_id != prompt.prompt_id:
            raise ValidationError(
                "response prompt_id does not match generated prompt."
            )
        if prompt.ground_truth is None:
            raise ValidationError(
                "generated prompt must include ground_truth for evaluation."
            )
        if len(prompt.ground_truth) != 1:
            raise ValidationError(
                "B2.7 evaluation currently requires one target value."
            )

        parsed = parse_prediction_response(response.response_text)
        target = prompt.ground_truth[0]
        prediction = parsed.prediction
        absolute_error = abs(float(prediction) - float(target))
        squared_error = absolute_error ** 2
        exact_match = prediction == target
        observed_correctness = 100.0 if exact_match else 0.0
        confidence_error = abs(float(parsed.confidence) - observed_correctness)

        identity_payload = {
            "prompt_sha256": prompt.prompt_sha256,
            "response_sha256": response.response_sha256,
            "parsed_sha256": parsed.parsed_sha256,
            "target": target,
            "exact_match": exact_match,
            "absolute_error": absolute_error,
            "squared_error": squared_error,
            "confidence_error": confidence_error,
        }
        evaluation_sha256 = stable_sha256(identity_payload)
        evaluation_id = (
            f"{prompt.prompt_id}:{response.model_id}:{evaluation_sha256[:16]}"
        )

        return EvaluationRecord(
            schema_version="1.0",
            evaluation_id=evaluation_id,
            evaluation_sha256=evaluation_sha256,
            prompt_id=prompt.prompt_id,
            prompt_sha256=prompt.prompt_sha256,
            response_sha256=response.response_sha256,
            model_id=response.model_id,
            prediction=prediction,
            target=target,
            confidence=parsed.confidence,
            explanation=parsed.explanation,
            exact_match=exact_match,
            absolute_error=absolute_error,
            squared_error=squared_error,
            confidence_error=confidence_error,
            metadata={
                "dataset_id": prompt.dataset_id,
                "case_id": prompt.case_id,
                "case_index": prompt.case_index,
                "template_id": prompt.template_id,
                "sequence_id": prompt.metadata.get("sequence_id"),
                "parsed_sha256": parsed.parsed_sha256,
                "response_metadata": dict(response.metadata or {}),
            },
        )

    def evaluate_batch(
        self,
        prompts: Sequence[GeneratedPrompt],
        responses: Sequence[RawModelResponse],
    ) -> EvaluationBatch:
        if len(prompts) != len(responses):
            raise ValidationError(
                "prompt and response batch lengths must match."
            )
        records = tuple(
            self.evaluate(prompt, response)
            for prompt, response in zip(prompts, responses)
        )
        return EvaluationBatch(records)
