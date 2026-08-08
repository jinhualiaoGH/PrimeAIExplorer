from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import mimetypes
import os
from pathlib import Path
import tempfile
from typing import Any, BinaryIO, Iterable, Mapping

from kernel.exceptions import ValidationError

from .contracts import ArtifactDescriptor


DEFAULT_CHUNK_SIZE = 1024 * 1024


def _require_positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{name} must be a positive integer.")
    return value


def _require_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("artifact name must be a non-empty string.")
    value = value.strip()
    if value in {".", ".."}:
        raise ValidationError("invalid artifact name.")
    if "\x00" in value:
        raise ValidationError("artifact name contains a null byte.")
    return value


def _require_media_type(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("media_type must be a non-empty string.")
    return value.strip()


def _sha256_stream(stream: BinaryIO, chunk_size: int) -> tuple[str, int, bytes]:
    chunk_size = _require_positive_int("chunk_size", chunk_size)

    digest = hashlib.sha256()
    size = 0
    buffer = io.BytesIO()

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        if not isinstance(chunk, (bytes, bytearray)):
            raise ValidationError("artifact stream must yield bytes.")
        chunk = bytes(chunk)
        digest.update(chunk)
        size += len(chunk)
        buffer.write(chunk)

    return digest.hexdigest(), size, buffer.getvalue()


def _hash_file(path: Path, chunk_size: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)

    return digest.hexdigest(), size


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    descriptor: ArtifactDescriptor
    blob_path: str
    deduplicated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "descriptor": self.descriptor.to_dict(),
            "blob_path": self.blob_path,
            "deduplicated": self.deduplicated,
        }


@dataclass(frozen=True, slots=True)
class ArtifactVerification:
    descriptor: ArtifactDescriptor
    exists: bool
    size_matches: bool
    sha256_matches: bool

    @property
    def valid(self) -> bool:
        return self.exists and self.size_matches and self.sha256_matches

    def to_dict(self) -> dict[str, Any]:
        return {
            "descriptor": self.descriptor.to_dict(),
            "exists": self.exists,
            "size_matches": self.size_matches,
            "sha256_matches": self.sha256_matches,
            "valid": self.valid,
        }


class DurableArtifactStore:
    """
    Immutable, content-addressed binary artifact store.

    Physical identity is SHA-256 of the artifact bytes. Artifact names,
    campaign IDs, experiment IDs, timestamps, and logical paths do not
    participate in content identity.
    """

    def __init__(self, root: str | Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.root = Path(root)
        self.blobs_root = self.root / "blobs"
        self.chunk_size = _require_positive_int("chunk_size", chunk_size)

    def initialize(self) -> None:
        self.blobs_root.mkdir(parents=True, exist_ok=True)

    def blob_path_for_sha256(self, sha256: str) -> Path:
        if not isinstance(sha256, str) or not re_full_sha256(sha256):
            raise ValidationError("sha256 must be a 64-character hexadecimal digest.")
        return (
            self.blobs_root
            / sha256[:2]
            / sha256[2:4]
            / sha256
        )

    def put_bytes(
        self,
        data: bytes | bytearray,
        *,
        name: str,
        media_type: str = "application/octet-stream",
        metadata: Mapping[str, Any] | None = None,
    ) -> StoredArtifact:
        if not isinstance(data, (bytes, bytearray)):
            raise ValidationError("data must be bytes or bytearray.")

        raw = bytes(data)
        sha256 = hashlib.sha256(raw).hexdigest()

        return self._persist_bytes(
            raw,
            sha256=sha256,
            name=name,
            media_type=media_type,
            metadata=metadata,
        )

    def put_stream(
        self,
        stream: BinaryIO,
        *,
        name: str,
        media_type: str = "application/octet-stream",
        metadata: Mapping[str, Any] | None = None,
    ) -> StoredArtifact:
        if not hasattr(stream, "read"):
            raise ValidationError("stream must provide read().")

        sha256, _, raw = _sha256_stream(stream, self.chunk_size)
        return self._persist_bytes(
            raw,
            sha256=sha256,
            name=name,
            media_type=media_type,
            metadata=metadata,
        )

    def put_file(
        self,
        source: str | Path,
        *,
        name: str | None = None,
        media_type: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> StoredArtifact:
        source = Path(source)
        if not source.is_file():
            raise FileNotFoundError(source)

        artifact_name = _require_name(name or source.name)
        artifact_media_type = (
            _require_media_type(media_type)
            if media_type is not None
            else (
                mimetypes.guess_type(artifact_name)[0]
                or "application/octet-stream"
            )
        )

        sha256, size = _hash_file(source, self.chunk_size)
        destination = self.blob_path_for_sha256(sha256)

        deduplicated = self._install_file(
            source=source,
            destination=destination,
            sha256=sha256,
            size=size,
        )

        descriptor = ArtifactDescriptor(
            name=artifact_name,
            media_type=artifact_media_type,
            sha256=sha256,
            size_bytes=size,
            relative_path=str(destination.relative_to(self.root)).replace("\\", "/"),
            metadata=dict(metadata or {}),
        )

        return StoredArtifact(
            descriptor=descriptor,
            blob_path=descriptor.relative_path,
            deduplicated=deduplicated,
        )

    def read_bytes(self, descriptor: ArtifactDescriptor) -> bytes:
        verification = self.verify(descriptor)
        if not verification.exists:
            raise FileNotFoundError(
                self.root / descriptor.relative_path
            )
        if not verification.valid:
            raise ValidationError(
                f"artifact integrity verification failed for {descriptor.name}."
            )
        return (self.root / descriptor.relative_path).read_bytes()

    def open(self, descriptor: ArtifactDescriptor) -> BinaryIO:
        verification = self.verify(descriptor)
        if not verification.exists:
            raise FileNotFoundError(
                self.root / descriptor.relative_path
            )
        if not verification.valid:
            raise ValidationError(
                f"artifact integrity verification failed for {descriptor.name}."
            )
        return (self.root / descriptor.relative_path).open("rb")

    def verify(self, descriptor: ArtifactDescriptor) -> ArtifactVerification:
        if not isinstance(descriptor, ArtifactDescriptor):
            raise ValidationError("descriptor must be ArtifactDescriptor.")

        expected = self.blob_path_for_sha256(descriptor.sha256)
        actual_path = self.root / descriptor.relative_path

        # Descriptors must point to their canonical content-addressed location.
        if actual_path.resolve() != expected.resolve():
            return ArtifactVerification(
                descriptor=descriptor,
                exists=actual_path.is_file(),
                size_matches=False,
                sha256_matches=False,
            )

        if not actual_path.is_file():
            return ArtifactVerification(
                descriptor=descriptor,
                exists=False,
                size_matches=False,
                sha256_matches=False,
            )

        sha256, size = _hash_file(actual_path, self.chunk_size)
        return ArtifactVerification(
            descriptor=descriptor,
            exists=True,
            size_matches=(size == descriptor.size_bytes),
            sha256_matches=(sha256 == descriptor.sha256),
        )

    def verify_many(
        self,
        descriptors: Iterable[ArtifactDescriptor],
    ) -> tuple[ArtifactVerification, ...]:
        return tuple(self.verify(item) for item in descriptors)

    def _persist_bytes(
        self,
        raw: bytes,
        *,
        sha256: str,
        name: str,
        media_type: str,
        metadata: Mapping[str, Any] | None,
    ) -> StoredArtifact:
        self.initialize()

        name = _require_name(name)
        media_type = _require_media_type(media_type)
        destination = self.blob_path_for_sha256(sha256)

        deduplicated = False
        if destination.exists():
            existing_sha, existing_size = _hash_file(destination, self.chunk_size)
            if existing_sha != sha256 or existing_size != len(raw):
                raise ValidationError(
                    "content-addressed destination exists with invalid content."
                )
            deduplicated = True
        else:
            self._atomic_write(destination, raw)

        descriptor = ArtifactDescriptor(
            name=name,
            media_type=media_type,
            sha256=sha256,
            size_bytes=len(raw),
            relative_path=str(destination.relative_to(self.root)).replace("\\", "/"),
            metadata=dict(metadata or {}),
        )
        return StoredArtifact(
            descriptor=descriptor,
            blob_path=descriptor.relative_path,
            deduplicated=deduplicated,
        )

    def _install_file(
        self,
        *,
        source: Path,
        destination: Path,
        sha256: str,
        size: int,
    ) -> bool:
        self.initialize()

        if destination.exists():
            existing_sha, existing_size = _hash_file(destination, self.chunk_size)
            if existing_sha != sha256 or existing_size != size:
                raise ValidationError(
                    "content-addressed destination exists with invalid content."
                )
            return True

        destination.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            prefix=destination.name + ".",
            suffix=".tmp",
            dir=str(destination.parent),
        )
        try:
            with source.open("rb") as input_handle, os.fdopen(fd, "wb") as output_handle:
                while True:
                    chunk = input_handle.read(self.chunk_size)
                    if not chunk:
                        break
                    output_handle.write(chunk)
                output_handle.flush()
                os.fsync(output_handle.fileno())

            temp_path = Path(temp_name)
            temp_sha, temp_size = _hash_file(temp_path, self.chunk_size)
            if temp_sha != sha256 or temp_size != size:
                raise ValidationError(
                    "artifact changed while being ingested."
                )

            os.replace(temp_name, destination)
            return False
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def re_full_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)
