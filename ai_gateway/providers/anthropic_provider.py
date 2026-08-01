from __future__ import annotations

import os
from typing import Any

from .base import ProviderAdapter, ProviderError, ProviderRequest, ProviderResponse
from .http_transport import JsonHttpTransport


class AnthropicProvider(ProviderAdapter):
    provider_name = "anthropic"

    def __init__(
        self,
        *,
        api_key_env: str = "ANTHROPIC_API_KEY",
        base_url: str = "https://api.anthropic.com",
        api_version: str = "2023-06-01",
        timeout_seconds: float = 120.0,
        transport: JsonHttpTransport | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
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
            "model": request.model,
            "max_tokens": request.max_output_tokens or 1024,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.metadata:
            payload["metadata"] = dict(request.metadata)

        response = self.transport.post_json(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self._api_key(),
                "anthropic-version": self.api_version,
            },
            payload=payload,
            timeout_seconds=self.timeout_seconds,
            provider=self.provider_name,
        )
        body = response.body
        text = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        usage = body.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = (
            input_tokens + output_tokens
            if isinstance(input_tokens, int) and isinstance(output_tokens, int)
            else None
        )
        return ProviderResponse(
            provider=self.provider_name,
            model=body.get("model", request.model),
            text=text,
            request_id=body.get("id"),
            finish_reason=body.get("stop_reason"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
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
