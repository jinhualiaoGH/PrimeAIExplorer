from __future__ import annotations

from .numpy_file import NumpyFileSequencePlugin


class PrimeGapSequencePlugin(NumpyFileSequencePlugin):
    plugin_id = "prime_gap"
    plugin_version = "1.0.0"
    display_name = "Prime Gaps"
    supported_representations = ("absolute",)

    def is_structurally_valid(self, value: int) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            and value % 2 == 0
        )
