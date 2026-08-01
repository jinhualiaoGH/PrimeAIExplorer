from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from kernel.exceptions import ValidationError


def file_sha256(
    path: Path,
    *,
    chunk_size: int = 8 * 1024 * 1024,
) -> str:
    if chunk_size <= 0:
        raise ValidationError("chunk_size must be positive.")
    digest = sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class NpyFileIdentity:
    schema_version: str
    filename: str
    byte_length: int
    dtype: str
    shape: tuple[int, ...]
    file_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValidationError(
                "Unsupported file identity schema version."
            )
        if not self.filename.strip():
            raise ValidationError("filename must not be empty.")
        if self.byte_length <= 0:
            raise ValidationError("byte_length must be positive.")
        if not self.dtype.strip():
            raise ValidationError("dtype must not be empty.")
        if len(self.shape) != 1 or self.shape[0] <= 0:
            raise ValidationError(
                "Memory-mapped sequences must be nonempty and 1D."
            )
        if len(self.file_sha256) != 64:
            raise ValidationError(
                "file_sha256 must contain 64 characters."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "filename": self.filename,
            "byte_length": self.byte_length,
            "dtype": self.dtype,
            "shape": list(self.shape),
            "file_sha256": self.file_sha256,
        }
