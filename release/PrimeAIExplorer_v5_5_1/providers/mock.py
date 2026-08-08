from __future__ import annotations

import json
import time
from typing import Any

from .base import ProviderResult


class MockConnector:
    name = "mock"

    def validate(self) -> None:
        return

    def execute(
        self,
        case: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> ProviderResult:
        del timeout_seconds
        started = time.perf_counter()
        payload = {
            "answer": case["mock_answer"],
            "confidence": case["mock_confidence"],
            "explanation": case["mock_explanation"],
        }
        return ProviderResult(
            provider=self.name,
            model="deterministic-v5",
            text=json.dumps(payload, ensure_ascii=False),
            latency_ms=round((time.perf_counter() - started) * 1000),
            usage={
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
            },
        )
