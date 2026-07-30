from __future__ import annotations

from plugins.left_twin import is_prime_64
from .numpy_file import NumpyFileSequencePlugin


class PrimeValueSequencePlugin(NumpyFileSequencePlugin):
    plugin_id = "prime_value"
    plugin_version = "1.0.0"
    display_name = "Prime Values"
    supported_representations = ("absolute", "gaps", "combined")

    def is_structurally_valid(self, value: int) -> bool:
        return is_prime_64(value)
