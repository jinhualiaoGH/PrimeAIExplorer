from __future__ import annotations

import os
from typing import Any

from .base import ProviderAdapter, ProviderError, ProviderRequest, ProviderResponse
from .http_transport import JsonHttpTransport


class OpenAIProvider(ProviderAdapter):
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "https://api.openai.com/v1",
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
        payload: dict[str, Any] = {"model": request.model, "input": request.prompt}
        if request.system_prompt:
            payload["instructions"] = request.system_prompt
        if request.max_output_tokens is not None:
            payload["max_output_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.metadata:
            payload["metadata"] = dict(request.metadata)
        if request.json_mode:
            payload["text"] = {"format": {"type": "json_object"}}

        response = self.transport.post_json(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self._api_key()}"},
            payload=payload,
            timeout_seconds=self.timeout_seconds,
            provider=self.provider_name,
        )
        body = response.body
        text = body.get("output_text")
        if not text:
            parts: list[str] = []
            for item in body.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            text = "".join(parts)

        usage = body.get("usage") or {}
        return ProviderResponse(
            provider=self.provider_name,
            model=body.get("model", request.model),
            text=text or "",
            request_id=body.get("id"),
            finish_reason=body.get("status"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
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
