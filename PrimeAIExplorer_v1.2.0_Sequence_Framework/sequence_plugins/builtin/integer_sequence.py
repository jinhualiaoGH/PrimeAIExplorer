from __future__ import annotations

from .numpy_file import NumpyFileSequencePlugin


class IntegerSequencePlugin(NumpyFileSequencePlugin):
    plugin_id = "integer_sequence"
    plugin_version = "1.0.0"
    display_name = "Canonical Integer Sequence"
    supported_representations = ("absolute", "gaps", "combined")
