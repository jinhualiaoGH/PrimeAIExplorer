from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderResult


class DeepSeekConnector:
    name = "deepseek"

    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.model = (
            os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()
            or "deepseek-v4-pro"
        )
        self.base_url = (
            os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
            or "https://api.deepseek.com"
        ).rstrip("/")

    def validate(self) -> None:
        if not self.api_key or self.api_key.startswith("replace-"):
            raise RuntimeError("DEEPSEEK_API_KEY is not configured.")

    def execute(
        self,
        case: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> ProviderResult:
        self.validate()

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": case["system"]},
                {"role": "user", "content": case["user"]},
            ],
            "response_format": {"type": "json_object"},
        }

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
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
            raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach DeepSeek: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("DeepSeek request timed out.") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("DeepSeek response did not contain choices.")

        message = choices[0].get("message") or {}
        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("DeepSeek response did not contain readable content.")

        usage = payload.get("usage") or {}
        return ProviderResult(
            provider=self.name,
            model=payload.get("model", self.model),
            text=text.strip(),
            latency_ms=round((time.perf_counter() - started) * 1000),
            usage={
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )
