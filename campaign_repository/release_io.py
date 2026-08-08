from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import zipfile

from kernel.exceptions import ValidationError


ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def sha256_bytes(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise ValidationError("data must be bytes.")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size <= 0
    ):
        raise ValidationError(
            "chunk_size must be a positive integer."
        )

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_zip_bytes(
    entries: dict[str, bytes],
) -> bytes:
    if not isinstance(entries, dict):
        raise ValidationError("entries must be a dict.")

    normalized: dict[str, bytes] = {}

    for raw_name, raw_data in entries.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValidationError(
                "zip entry names must be non-empty strings."
            )
        name = raw_name.replace("\\", "/").lstrip("/")
        if ".." in name.split("/"):
            raise ValidationError(
                "zip entry names cannot contain '..'."
            )
        if not isinstance(raw_data, bytes):
            raise ValidationError(
                "zip entry payloads must be bytes."
            )
        if name in normalized:
            raise ValidationError(
                f"duplicate zip entry: {name}"
            )
        normalized[name] = raw_data

    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_STORED,
        strict_timestamps=True,
    ) as archive:
        for name in sorted(normalized):
            info = zipfile.ZipInfo(
                filename=name,
                date_time=ZIP_EPOCH,
            )
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0
            archive.writestr(
                info,
                normalized[name],
            )
    return buffer.getvalue()


def write_immutable_bundle(
    path: str | Path,
    data: bytes,
) -> None:
    path = Path(path)
    if not isinstance(data, bytes):
        raise ValidationError("data must be bytes.")

    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = path.read_bytes()
        if existing == data:
            return
        raise ValidationError(
            f"immutable release bundle already exists with different content: {path}"
        )

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
