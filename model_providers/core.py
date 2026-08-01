from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Mapping, Protocol, Callable

@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    supports_system_prompt: bool = True
    supports_json_mode: bool = False
    supports_seed: bool = False

@dataclass(frozen=True, slots=True)
class ModelRequest:
    prompt: str
    model: str
    system_prompt: str | None = None
    temperature: float | None = 0.0
    max_output_tokens: int | None = None
    seed: int | None = None
    json_mode: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.prompt.strip(): raise ValueError("prompt must not be empty.")
        if not self.model.strip(): raise ValueError("model must not be empty.")
        if self.max_output_tokens is not None and self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive.")

@dataclass(frozen=True, slots=True)
class ProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    def to_dict(self): return asdict(self)

@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    latency_seconds: float
    request_id: str | None = None
    finish_reason: str | None = None
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    raw_response: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

class ModelProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities
    def generate(self, request: ModelRequest) -> ProviderResponse: ...

ProviderFactory = Callable[..., ModelProvider]

class ProviderRegistry:
    def __init__(self): self._factories: dict[str, ProviderFactory] = {}
    def register(self, name: str, factory: ProviderFactory):
        key = name.strip().lower()
        if not key: raise ValueError("provider name must not be empty.")
        if key in self._factories: raise ValueError(f"already registered: {key}")
        self._factories[key] = factory
    def create(self, name: str, **options):
        key = name.strip().lower()
        if key not in self._factories:
            raise KeyError(f"unknown provider: {key}")
        return self._factories[key](**options)
    def names(self): return tuple(sorted(self._factories))

def default_registry():
    from .providers import (
        OpenAIProvider, AnthropicProvider, GeminiProvider,
        GenericHttpProvider, ManualResponseProvider,
    )
    registry = ProviderRegistry()
    registry.register("openai", OpenAIProvider)
    registry.register("anthropic", AnthropicProvider)
    registry.register("gemini", GeminiProvider)
    registry.register("http", GenericHttpProvider)
    registry.register("manual", ManualResponseProvider)
    return registry
