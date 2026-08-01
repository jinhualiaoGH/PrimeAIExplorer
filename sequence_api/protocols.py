from __future__ import annotations

from typing import Protocol, runtime_checkable

from kernel.context import ExecutionContext
from sequence_api.models import (
    SequenceDescriptor,
    SequenceWindow,
    SequenceWindowRequest,
)


@runtime_checkable
class SequenceProvider(Protocol):
    sequence_id: str

    def describe(
        self,
        context: ExecutionContext,
    ) -> SequenceDescriptor:
        """Return immutable descriptive metadata."""

    def read_window(
        self,
        request: SequenceWindowRequest,
        context: ExecutionContext,
    ) -> SequenceWindow:
        """Return one deterministic sequence window."""
