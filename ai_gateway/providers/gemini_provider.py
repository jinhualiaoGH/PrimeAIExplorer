from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from .base import ProviderAdapter, ProviderError, ProviderRequest, ProviderResponse
from .http_transport import JsonHttpTransport


class GeminiProvider(ProviderAdapter):
    provider_name = "google"

    def __init__(
        self,
        *,
        api_key_env: str = "GEMINI_API_KEY",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 120.0,
        transport: JsonHttpTransport | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport or JsonHttpTransport()

    def _api_key(self) -> str:
        value = os.getenv(self.api_key_env)
        if not value:
            raise ProviderError(
                f"Environment variable {self.api_key_env} is not set.",
                provider=self.provider_name,
            )
        return value

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
        }
        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}

        generation: dict[str, Any] = {}
        if request.temperature is not None:
            generation["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            generation["maxOutputTokens"] = request.max_output_tokens
        if request.json_mode:
            generation["responseMimeType"] = "application/json"
        if generation:
            payload["generationConfig"] = generation

        model = request.model.removeprefix("models/")
        response = self.transport.post_json(
            f"{self.base_url}/models/{quote(model, safe='')}:generateContent",
            headers={"x-goog-api-key": self._api_key()},
            payload=payload,
            timeout_seconds=self.timeout_seconds,
            provider=self.provider_name,
        )
        body = response.body
        candidates = body.get("candidates") or []
        first = candidates[0] if candidates else {}
        text = "".join(
            part.get("text", "")
            for part in (first.get("content") or {}).get("parts", [])
            if "text" in part
        )
        usage = body.get("usageMetadata") or {}
        return ProviderResponse(
            provider=self.provider_name,
            model=request.model,
            text=text,
            request_id=response.headers.get("x-request-id"),
            finish_reason=first.get("finishReason"),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            total_tokens=usage.get("totalTokenCount"),
            provider_metadata={"status_code": response.status_code},
        )

    def health(self, *, live: bool = False) -> dict[str, Any]:
        configured = bool(os.getenv(self.api_key_env))
        return {
            "provider": self.provider_name,
            "configured": configured,
            "healthy": configured,
            "live_checked": False,
        }
