"""PrimeAIExplorer generic sequence-plugin framework."""

from .base import (
    CaseRecord,
    DatasetMetadata,
    PredictionEvaluation,
    SequencePlugin,
)
from .loader import PluginRegistry, load_plugin

__all__ = [
    "CaseRecord",
    "DatasetMetadata",
    "PredictionEvaluation",
    "SequencePlugin",
    "PluginRegistry",
    "load_plugin",
]
