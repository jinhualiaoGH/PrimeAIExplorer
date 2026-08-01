from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from kernel.context import ExecutionContext
from kernel.exceptions import ConfigurationError, ValidationError
from sequence_api.file_identity import NpyFileIdentity, file_sha256
from sequence_api.models import (
    SequenceDescriptor,
    SequenceValueType,
    SequenceWindow,
    SequenceWindowRequest,
)


@dataclass
class NpyMemmapSequenceProvider:
    sequence_id: str
    source_path: str
    title: str = "Memory-mapped NumPy sequence"
    sequence_version: str = "1.0.0"
    index_origin: int = 0
    strictly_increasing: bool = False
    expected_sha256: str | None = None
    metadata: Mapping[str, Any] | None = None
    _array: np.memmap | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _resolved_path: Path | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _identity: NpyFileIdentity | None = field(
        default=None,
        init=False,
        repr=False,
    )

    provider_type = "numpy_npy_memmap"

    def __post_init__(self) -> None:
        if not isinstance(self.sequence_id, str):
            raise ValidationError("sequence_id must be text.")
        self.sequence_id = self.sequence_id.strip()
        if not self.sequence_id:
            raise ValidationError(
                "sequence_id must not be empty."
            )
        if not isinstance(self.source_path, str):
            raise ValidationError("source_path must be text.")
        self.source_path = self.source_path.strip()
        if not self.source_path:
            raise ValidationError(
                "source_path must not be empty."
            )
        if isinstance(self.index_origin, bool) or not isinstance(
            self.index_origin,
            int,
        ):
            raise ValidationError(
                "index_origin must be an integer."
            )
        if not isinstance(self.strictly_increasing, bool):
            raise ValidationError(
                "strictly_increasing must be boolean."
            )
        if self.expected_sha256 is not None:
            normalized = self.expected_sha256.strip().lower()
            if len(normalized) != 64:
                raise ValidationError(
                    "expected_sha256 must contain 64 characters."
                )
            self.expected_sha256 = normalized
        self.metadata = dict(self.metadata or {})

    @classmethod
    def from_configuration(
        cls,
        configuration: Mapping[str, Any],
    ) -> "NpyMemmapSequenceProvider":
        if not isinstance(configuration, Mapping):
            raise ValidationError(
                "Provider configuration must be a mapping."
            )
        required = {"sequence_id", "source_path"}
        missing = sorted(required - set(configuration))
        if missing:
            raise ValidationError(
                f"Memmap provider is missing fields: {missing}"
            )
        return cls(
            sequence_id=configuration["sequence_id"],
            source_path=configuration["source_path"],
            title=configuration.get(
                "title",
                "Memory-mapped NumPy sequence",
            ),
            sequence_version=configuration.get(
                "sequence_version",
                "1.0.0",
            ),
            index_origin=configuration.get("index_origin", 0),
            strictly_increasing=configuration.get(
                "strictly_increasing",
                False,
            ),
            expected_sha256=configuration.get("expected_sha256"),
            metadata=configuration.get("metadata", {}),
        )

    def _path(self, context: ExecutionContext) -> Path:
        candidate = Path(self.source_path).expanduser()
        if not candidate.is_absolute():
            candidate = Path(context.project_root) / candidate
        return candidate.resolve()

    def _open(
        self,
        context: ExecutionContext,
    ) -> np.memmap:
        resolved = self._path(context)
        if self._array is not None:
            if resolved != self._resolved_path:
                raise ConfigurationError(
                    "Provider source path changed after mapping."
                )
            return self._array

        if not resolved.is_file():
            raise ConfigurationError(
                f"NumPy sequence file does not exist: {resolved}"
            )
        if resolved.suffix.lower() != ".npy":
            raise ConfigurationError(
                "Memory-mapped provider requires a .npy file."
            )

        try:
            array = np.load(
                resolved,
                mmap_mode="r",
                allow_pickle=False,
            )
        except Exception as exc:
            raise ConfigurationError(
                f"Could not memory-map NumPy sequence: {resolved}"
            ) from exc

        if not isinstance(array, np.memmap):
            raise ConfigurationError(
                "NumPy source was not opened as a memory map."
            )
        if array.ndim != 1:
            self._close_array(array)
            raise ValidationError(
                "Memory-mapped sequence must be one-dimensional."
            )
        if array.size == 0:
            self._close_array(array)
            raise ValidationError(
                "Memory-mapped sequence must not be empty."
            )
        if array.dtype.kind not in {"i", "u", "f"}:
            self._close_array(array)
            raise ValidationError(
                "Sequence dtype must be integer or floating point."
            )
        if array.flags.writeable:
            self._close_array(array)
            raise ValidationError(
                "Memory-mapped sequence must be read-only."
            )

        digest = file_sha256(resolved)
        if (
            self.expected_sha256 is not None
            and digest != self.expected_sha256
        ):
            self._close_array(array)
            raise ValidationError(
                "NumPy source SHA-256 does not match expectation."
            )

        self._array = array
        self._resolved_path = resolved
        self._identity = NpyFileIdentity(
            schema_version="1.0",
            filename=resolved.name,
            byte_length=resolved.stat().st_size,
            dtype=array.dtype.str,
            shape=tuple(int(item) for item in array.shape),
            file_sha256=digest,
        )
        return array

    @staticmethod
    def _close_array(array: np.memmap) -> None:
        mapping = getattr(array, "_mmap", None)
        if mapping is not None:
            mapping.close()


    def __enter__(self) -> "NpyMemmapSequenceProvider":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return self._array is not None

    @property
    def identity(self) -> NpyFileIdentity:
        if self._identity is None:
            raise ConfigurationError(
                "Provider has not opened its source."
            )
        return self._identity

    def describe(
        self,
        context: ExecutionContext,
    ) -> SequenceDescriptor:
        array = self._open(context)
        value_type = (
            SequenceValueType.REAL
            if array.dtype.kind == "f"
            else SequenceValueType.INTEGER
        )
        return SequenceDescriptor(
            schema_version="1.0",
            sequence_id=self.sequence_id,
            sequence_version=self.sequence_version,
            title=self.title,
            value_type=value_type,
            index_origin=self.index_origin,
            finite=True,
            length=int(array.size),
            strictly_increasing=self.strictly_increasing,
            metadata={
                **dict(self.metadata or {}),
                "provider": type(self).__name__,
                "source_type": self.provider_type,
                "read_only": True,
                "memory_mapped": True,
                "file_identity": self.identity.to_dict(),
            },
        )

    def read_window(
        self,
        request: SequenceWindowRequest,
        context: ExecutionContext,
    ) -> SequenceWindow:
        if request.sequence_id != self.sequence_id:
            raise ValidationError(
                "Window request sequence_id does not match provider."
            )
        array = self._open(context)
        offset = request.start_index - self.index_origin
        if offset < 0:
            raise ValidationError(
                "Window begins before the sequence index origin."
            )
        stop = offset + request.count
        if stop > array.size:
            raise ValidationError(
                "Window exceeds the finite sequence boundary."
            )

        view = array[offset:stop]
        if view.flags.writeable:
            raise ValidationError(
                "Window view unexpectedly became writeable."
            )
        if array.dtype.kind == "f":
            values = tuple(float(value) for value in view)
            value_type = SequenceValueType.REAL
        else:
            values = tuple(int(value) for value in view)
            value_type = SequenceValueType.INTEGER

        descriptor = self.describe(context)
        return SequenceWindow(
            descriptor_sha256=descriptor.descriptor_sha256,
            sequence_id=self.sequence_id,
            start_index=request.start_index,
            values=values,
            value_type=value_type,
        )

    def close(self) -> None:
        """Release the mapped file deterministically.

        Windows does not permit deleting a mapped file while any mmap handle
        remains open. Provider state is detached first, then the NumPy mmap is
        closed, references are deleted, and finalizers are collected.
        """
        import gc

        array = self._array
        self._array = None
        self._resolved_path = None
        self._identity = None

        if array is not None:
            mapping = getattr(array, "_mmap", None)
            if mapping is not None and not mapping.closed:
                mapping.close()
            del mapping
            del array

        gc.collect()
