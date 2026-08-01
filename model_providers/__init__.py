"""PrimeAIExplorer Phase C3 provider adapter layer."""
from .core import (
    ModelRequest, ProviderResponse, ProviderUsage, ProviderCapabilities,
    ModelProvider, ProviderRegistry, default_registry,
)
from .providers import (
    OpenAIProvider, AnthropicProvider, GeminiProvider,
    GenericHttpProvider, ManualResponseProvider,
)
from .bridge import ProviderExecutor, payload_prompt_builder

__all__ = [
    "ModelRequest", "ProviderResponse", "ProviderUsage",
    "ProviderCapabilities", "ModelProvider", "ProviderRegistry",
    "default_registry", "OpenAIProvider", "AnthropicProvider",
    "GeminiProvider", "GenericHttpProvider", "ManualResponseProvider",
    "ProviderExecutor", "payload_prompt_builder",
]
