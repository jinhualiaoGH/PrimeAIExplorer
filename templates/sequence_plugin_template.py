from __future__ import annotations

from pathlib import Path
from typing import Any


class ExampleSequencePlugin:
    plugin_id = "example_sequence"
    display_name = "Example Sequence"
    definition = "Document the exact mathematical definition."
    plugin_version = "0.1.0"
    supported_representations = ("absolute", "gaps", "combined")

    def validate_source(self) -> dict[str, Any]:
        raise NotImplementedError

    def build_dataset(self, request: Any) -> Path:
        raise NotImplementedError

    def validate_dataset(self, path: Path) -> dict[str, Any]:
        raise NotImplementedError

    def load_dataset(self, path: Path) -> Any:
        raise NotImplementedError

    def make_window(self, request: Any) -> Any:
        raise NotImplementedError

    def structural_validity(self, value: int) -> bool | None:
        return None

    def metadata(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "definition": self.definition,
        }
