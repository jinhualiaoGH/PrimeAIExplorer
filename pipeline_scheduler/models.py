from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ScheduledStage:
    name: str
    command: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    continue_on_failure: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ScheduledStage":
        name = str(value.get("name", "")).strip()
        if not name:
            raise ValueError("stage name is required")
        command = tuple(str(item) for item in value.get("command", []))
        if not command:
            raise ValueError(f"stage {name!r} requires a non-empty command")
        dependencies = tuple(str(item) for item in value.get("depends_on", []))
        return cls(
            name=name,
            command=command,
            depends_on=dependencies,
            continue_on_failure=bool(value.get("continue_on_failure", False)),
            metadata=dict(value.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": list(self.command),
            "depends_on": list(self.depends_on),
            "continue_on_failure": self.continue_on_failure,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class SchedulerSpecification:
    name: str
    stages: tuple[ScheduledStage, ...]
    max_parallel: int = 1
    schema_version: str = "1.0"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SchedulerSpecification":
        name = str(value.get("name", "")).strip() or "PrimeAIExplorer scheduled pipeline"
        max_parallel = int(value.get("max_parallel", 1))
        if max_parallel < 1:
            raise ValueError("max_parallel must be at least 1")
        stages = tuple(ScheduledStage.from_dict(item) for item in value.get("stages", []))
        if not stages:
            raise ValueError("at least one stage is required")
        return cls(
            name=name,
            stages=stages,
            max_parallel=max_parallel,
            schema_version=str(value.get("schema_version", "1.0")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "max_parallel": self.max_parallel,
            "stages": [stage.to_dict() for stage in self.stages],
        }
