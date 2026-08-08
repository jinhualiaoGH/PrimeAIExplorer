from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderResult
from .common import extract_openai_response_text


class OpenAIConnector:
    name = "openai"

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5").strip() or "gpt-5"

    def validate(self) -> None:
        if not self.api_key or self.api_key.startswith("replace-"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")

    def execute(
        self,
        case: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> ProviderResult:
        self.validate()

        body = {
            "model": self.model,
            "input": [
                {"role": "system", "content": case["system"]},
                {"role": "user", "content": case["user"]},
            ],
        }

        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach OpenAI: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("OpenAI request timed out.") from exc

        usage = payload.get("usage") or {}
        return ProviderResult(
            provider=self.name,
            model=payload.get("model", self.model),
            text=extract_openai_response_text(payload),
            latency_ms=round((time.perf_counter() - started) * 1000),
            usage={
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )
