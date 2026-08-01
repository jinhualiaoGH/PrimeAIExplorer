from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv

from kernel.context import ExecutionContext
from kernel.exceptions import ConfigurationError, ValidationError
from kernel.serialization import stable_sha256
from sequence_api.gap_manifest import GapPartition, GapRepositoryManifest
from sequence_api.gap_provider import PartitionedGapSequenceProvider


_DEFAULT_ALIASES = {
    "path": (
        "path",
        "file",
        "file_path",
        "filepath",
        "gap_file",
        "gap_path",
        "filename",
        "file_name",
    ),
    "count": (
        "count",
        "gap_count",
        "length",
        "record_count",
        "records",
        "num_gaps",
    ),
    "start_index": (
        "start_index",
        "index_start",
        "first_index",
        "gap_start_index",
        "prime_index_start",
    ),
    "ordinal": (
        "ordinal",
        "partition",
        "partition_id",
        "partition_index",
        "file_index",
        "block",
        "block_index",
    ),
    "sha256": (
        "sha256",
        "sha_256",
        "file_sha256",
        "checksum_sha256",
    ),
}


@dataclass(frozen=True)
class PrimeNetColumnMapping:
    path: str
    count: str
    start_index: str | None = None
    ordinal: str | None = None
    sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "count": self.count,
            "start_index": self.start_index,
            "ordinal": self.ordinal,
            "sha256": self.sha256,
        }


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _detect_column(
    normalized_to_original: Mapping[str, str],
    logical_name: str,
    *,
    required: bool,
) -> str | None:
    for alias in _DEFAULT_ALIASES[logical_name]:
        normalized = _normalize_header(alias)
        if normalized in normalized_to_original:
            return normalized_to_original[normalized]
    if required:
        raise ValidationError(
            f"PrimeNet manifest is missing a recognizable {logical_name!r} column."
        )
    return None


def detect_primenet_columns(headers: Sequence[str]) -> PrimeNetColumnMapping:
    if not headers:
        raise ValidationError("PrimeNet manifest has no header row.")
    normalized_to_original: dict[str, str] = {}
    for header in headers:
        normalized = _normalize_header(header)
        if normalized in normalized_to_original:
            raise ValidationError("PrimeNet manifest contains duplicate normalized headers.")
        normalized_to_original[normalized] = header
    return PrimeNetColumnMapping(
        path=_detect_column(normalized_to_original, "path", required=True),
        count=_detect_column(normalized_to_original, "count", required=True),
        start_index=_detect_column(
            normalized_to_original, "start_index", required=False
        ),
        ordinal=_detect_column(normalized_to_original, "ordinal", required=False),
        sha256=_detect_column(normalized_to_original, "sha256", required=False),
    )


@dataclass
class PrimeNetGapRepositoryAdapter:
    sequence_id: str
    repository_root: str
    manifest_path: str
    repository_id: str = "primenet-gap-repository"
    repository_version: str = "unknown"
    index_origin: int = 1
    cache_size: int = 4
    verify_partition_sha256: bool = False
    column_mapping: Mapping[str, str | None] | None = None
    title: str = "PrimeNet canonical prime-gap sequence"
    sequence_version: str = "1.0.0"
    metadata: Mapping[str, Any] | None = None
    _provider: PartitionedGapSequenceProvider | None = field(
        default=None, init=False, repr=False
    )
    _adapter_identity: str | None = field(default=None, init=False, repr=False)

    provider_type = "primenet_gap_repository"

    def __post_init__(self) -> None:
        self.sequence_id = self.sequence_id.strip()
        self.repository_root = self.repository_root.strip()
        self.manifest_path = self.manifest_path.strip()
        if not self.sequence_id:
            raise ValidationError("sequence_id must not be empty.")
        if not self.repository_root:
            raise ValidationError("repository_root must not be empty.")
        if not self.manifest_path:
            raise ValidationError("manifest_path must not be empty.")
        if isinstance(self.index_origin, bool) or not isinstance(self.index_origin, int):
            raise ValidationError("index_origin must be an integer.")
        if isinstance(self.cache_size, bool) or not isinstance(self.cache_size, int):
            raise ValidationError("cache_size must be an integer.")
        if self.cache_size <= 0:
            raise ValidationError("cache_size must be positive.")
        self.metadata = dict(self.metadata or {})

    @classmethod
    def from_configuration(
        cls, configuration: Mapping[str, Any]
    ) -> "PrimeNetGapRepositoryAdapter":
        if not isinstance(configuration, Mapping):
            raise ValidationError("provider configuration must be a mapping.")
        required = {"sequence_id", "repository_root", "manifest_path"}
        missing = sorted(required - set(configuration))
        if missing:
            raise ValidationError(f"PrimeNet adapter is missing fields: {missing}")
        return cls(
            sequence_id=configuration["sequence_id"],
            repository_root=configuration["repository_root"],
            manifest_path=configuration["manifest_path"],
            repository_id=configuration.get(
                "repository_id", "primenet-gap-repository"
            ),
            repository_version=configuration.get(
                "repository_version", "unknown"
            ),
            index_origin=configuration.get("index_origin", 1),
            cache_size=configuration.get("cache_size", 4),
            verify_partition_sha256=configuration.get(
                "verify_partition_sha256", False
            ),
            column_mapping=configuration.get("column_mapping"),
            title=configuration.get(
                "title", "PrimeNet canonical prime-gap sequence"
            ),
            sequence_version=configuration.get("sequence_version", "1.0.0"),
            metadata=configuration.get("metadata", {}),
        )

    def _resolve(self, value: str, context: ExecutionContext) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = Path(context.project_root) / candidate
        return candidate.resolve()

    def _resolve_repository_root(self, context: ExecutionContext) -> Path:
        root = self._resolve(self.repository_root, context)
        if not root.is_dir():
            raise ConfigurationError(f"PrimeNet repository root does not exist: {root}")
        return root

    def _resolve_manifest_path(
        self, repository_root: Path, context: ExecutionContext
    ) -> Path:
        candidate = Path(self.manifest_path).expanduser()
        if not candidate.is_absolute():
            candidate = repository_root / candidate
        candidate = candidate.resolve()
        if not candidate.is_file():
            raise ConfigurationError(
                f"PrimeNet repository manifest does not exist: {candidate}"
            )
        return candidate

    def _mapping_from_headers(self, headers: Sequence[str]) -> PrimeNetColumnMapping:
        if self.column_mapping is None:
            return detect_primenet_columns(headers)
        supplied = dict(self.column_mapping)
        mapping = PrimeNetColumnMapping(
            path=supplied.get("path") or "",
            count=supplied.get("count") or "",
            start_index=supplied.get("start_index"),
            ordinal=supplied.get("ordinal"),
            sha256=supplied.get("sha256"),
        )
        if not mapping.path or not mapping.count:
            raise ValidationError(
                "column_mapping must define at least 'path' and 'count'."
            )
        missing = [
            column
            for column in mapping.to_dict().values()
            if column is not None and column not in headers
        ]
        if missing:
            raise ValidationError(
                f"configured PrimeNet columns are missing: {sorted(missing)}"
            )
        return mapping

    @staticmethod
    def _parse_int(row: Mapping[str, str], column: str, label: str) -> int:
        raw = row.get(column, "")
        try:
            value = int(raw)
        except Exception as exc:
            raise ValidationError(
                f"PrimeNet manifest {label} is not an integer: {raw!r}"
            ) from exc
        return value

    def translate_manifest(
        self, context: ExecutionContext
    ) -> GapRepositoryManifest:
        repository_root = self._resolve_repository_root(context)
        manifest_file = self._resolve_manifest_path(repository_root, context)
        try:
            with manifest_file.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                headers = tuple(reader.fieldnames or ())
                mapping = self._mapping_from_headers(headers)
                raw_rows = list(reader)
        except (ConfigurationError, ValidationError):
            raise
        except Exception as exc:
            raise ConfigurationError(
                f"could not read PrimeNet CSV manifest: {manifest_file}"
            ) from exc

        if not raw_rows:
            raise ValidationError("PrimeNet manifest contains no partition rows.")

        parsed: list[dict[str, Any]] = []
        running_start = self.index_origin
        for position, row in enumerate(raw_rows):
            ordinal = (
                self._parse_int(row, mapping.ordinal, "ordinal")
                if mapping.ordinal
                else position
            )
            count = self._parse_int(row, mapping.count, "count")
            start_index = (
                self._parse_int(row, mapping.start_index, "start_index")
                if mapping.start_index
                else running_start
            )
            path_text = (row.get(mapping.path) or "").strip()
            if not path_text:
                raise ValidationError("PrimeNet manifest partition path is empty.")
            source_path = Path(path_text).expanduser()
            if not source_path.is_absolute():
                source_path = repository_root / source_path
            source_path = source_path.resolve()
            # The translated manifest is written below
            # <repository_root>/.primeaiexplorer. Store a canonical absolute
            # path so partition resolution is independent of that generated
            # manifest location.
            manifest_path_text = str(source_path)

            sha256 = None
            if mapping.sha256:
                raw_sha = (row.get(mapping.sha256) or "").strip().lower()
                sha256 = raw_sha or None

            parsed.append({
                "ordinal": ordinal,
                "start_index": start_index,
                "count": count,
                "path": manifest_path_text,
                "sha256": sha256,
            })
            running_start = start_index + count

        parsed.sort(key=lambda item: item["ordinal"])
        partitions = tuple(
            GapPartition(
                ordinal=item["ordinal"],
                start_index=item["start_index"],
                count=item["count"],
                path=item["path"],
                sha256=item["sha256"],
            )
            for item in parsed
        )

        adapter_payload = {
            "provider_type": self.provider_type,
            "repository_root": str(repository_root),
            "source_manifest": str(manifest_file),
            "column_mapping": mapping.to_dict(),
            "repository_id": self.repository_id,
            "repository_version": self.repository_version,
            "index_origin": self.index_origin,
            "partitions": [item.to_dict() for item in partitions],
        }
        self._adapter_identity = stable_sha256(adapter_payload)

        return GapRepositoryManifest(
            schema_version="1.0",
            repository_id=self.repository_id,
            repository_version=self.repository_version,
            dtype="uint16",
            index_origin=self.index_origin,
            partitions=partitions,
            metadata={
                **dict(self.metadata or {}),
                "adapter": type(self).__name__,
                "adapter_sha256": self._adapter_identity,
                "source_manifest": str(manifest_file),
                "repository_root": str(repository_root),
                "column_mapping": mapping.to_dict(),
            },
        )

    @property
    def adapter_sha256(self) -> str:
        if self._adapter_identity is None:
            raise ConfigurationError("PrimeNet adapter has not been initialized.")
        return self._adapter_identity

    def _ensure_provider(
        self, context: ExecutionContext
    ) -> PartitionedGapSequenceProvider:
        if self._provider is not None:
            return self._provider
        translated = self.translate_manifest(context)
        repository_root = self._resolve_repository_root(context)
        generated_manifest = repository_root / ".primeaiexplorer" / (
            f"{self.sequence_id}_translated_gap_manifest.json"
        )
        generated_manifest.parent.mkdir(parents=True, exist_ok=True)
        generated_manifest.write_text(
            __import__("json").dumps(translated.to_dict(), indent=2),
            encoding="utf-8",
        )
        self._provider = PartitionedGapSequenceProvider(
            sequence_id=self.sequence_id,
            manifest_path=str(generated_manifest),
            title=self.title,
            sequence_version=self.sequence_version,
            cache_size=self.cache_size,
            verify_partition_sha256=self.verify_partition_sha256,
            metadata={
                **dict(self.metadata or {}),
                "source_type": self.provider_type,
                "adapter_sha256": self.adapter_sha256,
                "translated_manifest": str(generated_manifest),
            },
        )
        return self._provider

    @property
    def open_partition_count(self) -> int:
        if self._provider is None:
            return 0
        return self._provider.open_partition_count

    def describe(self, context: ExecutionContext):
        descriptor = self._ensure_provider(context).describe(context)
        metadata = dict(descriptor.metadata)
        metadata.update({
            "provider": type(self).__name__,
            "source_type": self.provider_type,
            "adapter_sha256": self.adapter_sha256,
        })
        return type(descriptor)(
            schema_version=descriptor.schema_version,
            sequence_id=descriptor.sequence_id,
            sequence_version=descriptor.sequence_version,
            title=descriptor.title,
            value_type=descriptor.value_type,
            index_origin=descriptor.index_origin,
            finite=descriptor.finite,
            length=descriptor.length,
            strictly_increasing=descriptor.strictly_increasing,
            metadata=metadata,
        )

    def read_window(self, request, context: ExecutionContext):
        return self._ensure_provider(context).read_window(request, context)

    def close(self) -> None:
        if self._provider is not None:
            self._provider.close()
        self._provider = None
        self._adapter_identity = None

    def __enter__(self) -> "PrimeNetGapRepositoryAdapter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
