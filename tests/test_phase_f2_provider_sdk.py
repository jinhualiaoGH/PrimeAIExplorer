from __future__ import annotations

from dataclasses import dataclass

from ai_gateway.providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAIProvider,
    ProviderRequest,
)
from ai_gateway.providers.http_transport import JsonHttpResponse


@dataclass
class FakeTransport:
    body: dict

    def post_json(self, url, *, headers, payload, timeout_seconds, provider):
        self.url = url
        self.headers = headers
        self.payload = payload
        self.provider = provider
        return JsonHttpResponse(200, {"x-request-id": "req-test"}, self.body)


def test_openai_normalization(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    transport = FakeTransport({
        "id": "resp-1",
        "model": "gpt-test",
        "status": "completed",
        "output_text": "{\"prediction\":6}",
        "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    })
    result = OpenAIProvider(transport=transport).invoke(
        ProviderRequest(model="gpt-test", prompt="Predict.", json_mode=True)
    )
    assert result.provider == "openai"
    assert result.text == '{"prediction":6}'
    assert result.total_tokens == 15
    assert transport.url.endswith("/responses")


def test_anthropic_normalization(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    transport = FakeTransport({
        "id": "msg-1",
        "model": "claude-test",
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": "{\"prediction\":6}"}],
        "usage": {"input_tokens": 8, "output_tokens": 4},
    })
    result = AnthropicProvider(transport=transport).invoke(
        ProviderRequest(model="claude-test", prompt="Predict.")
    )
    assert result.provider == "anthropic"
    assert result.text == '{"prediction":6}'
    assert result.total_tokens == 12
    assert transport.url.endswith("/v1/messages")


def test_gemini_normalization(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    transport = FakeTransport({
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": "{\"prediction\":6}"}]},
        }],
        "usageMetadata": {
            "promptTokenCount": 7,
            "candidatesTokenCount": 3,
            "totalTokenCount": 10,
        },
    })
    result = GeminiProvider(transport=transport).invoke(
        ProviderRequest(model="gemini-test", prompt="Predict.", json_mode=True)
    )
    assert result.provider == "google"
    assert result.text == '{"prediction":6}'
    assert result.total_tokens == 10
    assert transport.url.endswith("/models/gemini-test:generateContent")


def test_offline_health_reflects_configuration(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert OpenAIProvider().health()["configured"] is False
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    assert OpenAIProvider().health()["configured"] is True
