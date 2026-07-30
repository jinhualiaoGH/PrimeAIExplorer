"""Shared observatory interface for PrimeAIExplorer v1.0."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from .result import ObservatoryResult


class Observatory(ABC):
    """Base interface implemented by every scientific observatory.

    Subclasses must declare a non-empty ``name`` and may override ``version``.
    The manager passes canonical analysis records and a read-only-style context
    mapping to :meth:`analyze`.
    """

    name: ClassVar[str]
    version: ClassVar[str] = "1.0.0"

    @abstractmethod
    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        """Analyze canonical records and return an :class:`ObservatoryResult`."""
