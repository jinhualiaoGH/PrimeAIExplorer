from __future__ import annotations

from typing import Any


class ExampleConnector:
    connector_id = "example"
    provider = "example"
    model_id = "example-model"
    connector_version = "0.1.0"
    pricing_class = "local"
    supports_structured_output = True
    supports_tools = False

    def validate(self) -> dict[str, Any]:
        return {"valid": True}

    def capabilities(self) -> dict[str, Any]:
        return {
            "structured_output": self.supports_structured_output,
            "tools": self.supports_tools,
        }

    def execute(self, request: Any) -> Any:
        raise NotImplementedError
