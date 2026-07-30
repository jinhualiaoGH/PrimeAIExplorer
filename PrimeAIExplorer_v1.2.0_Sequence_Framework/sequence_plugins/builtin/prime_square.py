from __future__ import annotations

from math import isqrt
from typing import Any, Mapping

from plugins.left_twin import is_prime_64
from .numpy_file import NumpyFileSequencePlugin


class PrimeSquareSequencePlugin(NumpyFileSequencePlugin):
    plugin_id = "prime_square"
    plugin_version = "1.0.0"
    display_name = "Squares of Prime Values"
    supported_representations = ("absolute", "gaps", "combined")

    def transform_source_value(
        self,
        value: int,
        *,
        options: Mapping[str, Any] | None = None,
    ) -> int:
        squared = value * value
        if squared > 0xFFFFFFFFFFFFFFFF:
            raise OverflowError(
                f"Prime square exceeds uint64 capacity: {value}^2"
            )
        return squared

    def is_structurally_valid(self, value: int) -> bool:
        if value < 4:
            return False
        root = isqrt(value)
        return root * root == value and is_prime_64(root)
