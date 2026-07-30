from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from core.models import SequenceWindow


class SequencePlugin(ABC):
    plugin_name: str
    display_name: str
    definition: str

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def validate_source(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_dataset(self, overwrite: bool = False) -> Path:
        raise NotImplementedError

    @abstractmethod
    def load_dataset(self) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def make_window(
        self,
        endpoint_index_1_based: int,
        window_size: int,
        representation: str,
    ) -> SequenceWindow:
        raise NotImplementedError

    def structural_validity(self, prediction: int) -> bool | None:
        return None

    def baseline_predictions(self, window: SequenceWindow) -> dict[str, int]:
        values = window.observed
        result: dict[str, int] = {}

        if window.representation == "absolute":
            if len(values) >= 2:
                last_gap = values[-1] - values[-2]
                result["repeat_last_delta"] = values[-1] + last_gap
                deltas = np.diff(np.asarray(values, dtype=np.int64))
                result["median_delta"] = values[-1] + int(np.median(deltas))
                result["mean_delta"] = values[-1] + int(round(float(np.mean(deltas))))
        elif window.representation in {"gaps", "combined"}:
            if window.current_value is not None and values:
                result["repeat_last_gap"] = window.current_value + values[-1]
                result["median_gap"] = window.current_value + int(np.median(values))
                result["mean_gap"] = window.current_value + int(round(float(np.mean(values))))
        return result
