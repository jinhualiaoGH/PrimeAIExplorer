from __future__ import annotations

from typing import Any


class ExampleEvaluator:
    metric_id = "example_metric"
    evaluator_version = "0.1.0"

    def score(
        self,
        *,
        prediction: Any,
        target: Any,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError
