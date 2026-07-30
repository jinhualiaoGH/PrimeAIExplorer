from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SequenceWindow:
    endpoint_index_1_based: int
    target_index_1_based: int
    window_size: int
    representation: str
    observed: list[int]
    current_value: int | None
    target_value: int


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    experiment_id: str
    sequence_plugin: str
    endpoint_index_1_based: int
    target_index_1_based: int
    window_size: int
    representation: str
    definition_condition: str
    payload: dict[str, Any]
    target_value: int
