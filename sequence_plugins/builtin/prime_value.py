from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json
import os
import random
import re
import uuid

import numpy as np
from numpy.lib.format import open_memmap

from plugins.left_twin import is_prime_64
from sequence_plugins.base import DatasetMetadata, SequencePlugin

_PARTITION_PATTERN = re.compile(
    r"^primes_(?P<start>[0-9]+)_(?P<end>[0-9]+)\.npy$", re.IGNORECASE
)

@dataclass(frozen=True)
class PrimePartition:
    path: Path
    start: int
    end: int
    count: int
    dtype: str
    first_prime: int
    last_prime: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _sha256_file(path: Path, *, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8'
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _resolve_path(value: str | Path, *, experiment_root: Path | None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and experiment_root is not None:
        path = experiment_root / path
    return path.resolve()


class PrimeValueSequencePlugin(SequencePlugin):
    plugin_id = 'prime_value'
    plugin_version = '1.3.0'
    display_name = 'Prime Values'
    supported_representations = ('absolute',)

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self._config = dict(config) if config is not None else None

    def configure(self, config: Mapping[str, Any]) -> 'PrimeValueSequencePlugin':
        self._config = dict(config)
        return self

    def _configuration(self, options: Mapping[str, Any] | None = None) -> dict[str, Any]:
        config = dict(options) if options is not None else self._config
        if config is None:
            raise ValueError('PrimeValueSequencePlugin requires EXP-000003 configuration.')
        return config

    def _experiment_root(self, config: Mapping[str, Any]) -> Path | None:
        raw = config.get('_experiment_root')
        return Path(raw).resolve() if raw else None

    def _prime_root(self, source: Path | None, config: Mapping[str, Any]) -> Path:
        configured = config.get('repository', {}).get('prime_root')
        if configured:
            return _resolve_path(configured, experiment_root=self._experiment_root(config))
        if source is None:
            raise ValueError('PrimeNet prime_root is missing.')
        return Path(source).expanduser().resolve()

    def _required_count(self, required_count: int | None, config: Mapping[str, Any]) -> int:
        result = int(required_count if required_count is not None else config.get('sequence', {}).get('target_count', 0))
        if result <= 0:
            raise ValueError('Required prime count must be positive.')
        return result

    def _metadata_path(self, dataset: Path, config: Mapping[str, Any]) -> Path:
        configured = config.get('sequence', {}).get('metadata_file')
        if configured:
            return _resolve_path(configured, experiment_root=self._experiment_root(config))
        return dataset.with_suffix('.metadata.json')

    def discover_partitions(self, prime_root: Path) -> list[tuple[Path, int, int]]:
        if not prime_root.exists(): raise FileNotFoundError(f'Prime root does not exist: {prime_root}')
        if not prime_root.is_dir(): raise NotADirectoryError(f'Prime root is not a directory: {prime_root}')
        found = []
        for path in prime_root.iterdir():
            if not path.is_file(): continue
            match = _PARTITION_PATTERN.fullmatch(path.name)
            if match:
                start, end = int(match.group('start')), int(match.group('end'))
                if start > end: raise ValueError(f'Invalid partition range: {path.name}')
                found.append((path, start, end))
        found.sort(key=lambda x: (x[1], x[2], x[0].name.casefold()))
        if not found: raise ValueError(f'No canonical partitions found: {prime_root}')
        seen = set()
        for path, start, end in found:
            if (start, end) in seen: raise ValueError(f'Duplicate partition range: {start}-{end}')
            seen.add((start, end))
        return found

    @staticmethod
    def validate_partition_adjacency(found: Sequence[tuple[Path, int, int]]) -> None:
        for previous, current in zip(found, found[1:]):
            if current[1] != previous[2] + 1:
                raise ValueError(
                    'PrimeNet partition adjacency failure: '
                    f'{previous[0].name} ends at {previous[2]:,}; '
                    f'{current[0].name} starts at {current[1]:,}.'
                )

    def inspect_partition(self, path: Path, start: int, end: int, *, full_monotonic_check: bool) -> PrimePartition:
        values = np.load(path, mmap_mode='r', allow_pickle=False)
        if values.ndim != 1: raise ValueError(f'Prime partition is not one-dimensional: {path}')
        if values.dtype.kind != 'u': raise ValueError(f'Prime partition must use unsigned integer dtype: {path} ({values.dtype})')
        if len(values) == 0: raise ValueError(f'Prime partition is empty: {path}')
        first, last = int(values[0]), int(values[-1])
        if not start <= first <= end: raise ValueError(f'First prime outside filename range: {path.name}')
        if not start <= last <= end: raise ValueError(f'Last prime outside filename range: {path.name}')
        if full_monotonic_check and len(values) > 1 and not bool(np.all(values[1:] > values[:-1])):
            raise ValueError(f'Prime partition is not strictly increasing: {path}')
        return PrimePartition(path, start, end, int(len(values)), str(values.dtype), first, last)

    def _inspect_source(self, source: Path, config: Mapping[str, Any], *, full_monotonic: bool) -> list[PrimePartition]:
        root = self._prime_root(source, config)
        found = self.discover_partitions(root)
        self.validate_partition_adjacency(found)
        partitions, previous_last = [], None
        for path, start, end in found:
            p = self.inspect_partition(path, start, end, full_monotonic_check=full_monotonic)
            if previous_last is not None and p.first_prime <= previous_last:
                raise ValueError(f'Prime values are not increasing across boundary before {path.name}.')
            partitions.append(p)
            previous_last = p.last_prime
        return partitions

    def validate_source(self, source: Path, *, required_count: int | None = None, options: Mapping[str, Any] | None = None) -> dict[str, Any]:
        config = self._configuration(options)
        required = self._required_count(required_count, config)
        full = bool(config.get('validation', {}).get('full_partition_monotonic_check', False))
        partitions = self._inspect_source(source, config, full_monotonic=full)
        available = sum(p.count for p in partitions)
        manifest_value = config.get('repository', {}).get('manifest')
        manifest = _resolve_path(manifest_value, experiment_root=self._experiment_root(config)) if manifest_value else None
        return {
            'plugin_id': self.plugin_id, 'plugin_version': self.plugin_version,
            'source_type': 'primenet_prime_repository',
            'prime_root': str(self._prime_root(source, config)),
            'partition_count': len(partitions), 'available_prime_count': available,
            'required_prime_count': required, 'sufficient': available >= required,
            'first_prime': partitions[0].first_prime,
            'last_available_prime': partitions[-1].last_prime,
            'first_partition': partitions[0].path.name,
            'last_partition': partitions[-1].path.name,
            'source_manifest': str(manifest) if manifest else None,
            'source_manifest_exists': bool(manifest and manifest.is_file()),
            'source_manifest_sha256': _sha256_file(manifest) if manifest and manifest.is_file() else None,
            'full_partition_monotonic_check': full, 'read_only': True, 'valid': True,
        }

    def plan_dataset(self, source: Path, destination: Path, *, count: int, options: Mapping[str, Any] | None = None) -> dict[str, Any]:
        config = self._configuration(options)
        source_result = self.validate_source(source, required_count=count, options=config)
        destination = Path(destination).expanduser().resolve()
        metadata = self._metadata_path(destination, config)
        return {
            'plugin_id': self.plugin_id, 'plugin_version': self.plugin_version,
            'source': source_result['prime_root'], 'destination': str(destination),
            'metadata': str(metadata), 'count': int(count), 'dtype': 'uint64',
            'estimated_data_bytes': int(count) * 8,
            'source_sufficient': source_result['sufficient'],
            'would_replace_dataset': destination.exists(),
            'would_replace_metadata': metadata.exists(), 'writes_performed': False,
        }

    def build_dataset(self, source: Path, destination: Path, *, count: int, options: Mapping[str, Any] | None = None) -> DatasetMetadata:
        config = self._configuration(options)
        count = int(count)
        if count <= 0: raise ValueError('count must be positive.')
        destination = Path(destination).expanduser().resolve()
        metadata_path = self._metadata_path(destination, config)
        overwrite = bool(config.get('build', {}).get('overwrite', False))
        if (destination.exists() or metadata_path.exists()) and not overwrite:
            raise FileExistsError('Dataset or metadata already exists; explicit overwrite is required.')

        full = bool(config.get('validation', {}).get('full_partition_monotonic_check', False))
        partitions = self._inspect_source(source, config, full_monotonic=full)
        available = sum(p.count for p in partitions)
        if available < count:
            raise ValueError(f'PrimeNet source contains {available:,} primes; {count:,} required.')

        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        temporary_dataset = destination.with_name(f'.{destination.name}.{token}.tmp.npy')
        started = _utc_now()
        written = 0
        try:
            output = open_memmap(temporary_dataset, mode='w+', dtype=np.uint64, shape=(count,))
            for partition in partitions:
                if written >= count: break
                values = np.load(partition.path, mmap_mode='r', allow_pickle=False)
                take = min(len(values), count - written)
                output[written:written + take] = values[:take]
                written += take
            output.flush()
            del output
            if written != count: raise RuntimeError(f'Internal copy count mismatch: {written:,} != {count:,}')
            staged = np.load(temporary_dataset, mmap_mode='r', allow_pickle=False)
            if staged.dtype != np.dtype(np.uint64) or staged.ndim != 1 or len(staged) != count:
                raise RuntimeError('Staged dataset shape or dtype validation failed.')
            first, second_last, last = int(staged[0]), int(staged[-2]) if count > 1 else None, int(staged[-1])
            del staged
            dataset_sha = _sha256_file(temporary_dataset)
            os.replace(temporary_dataset, destination)

            manifest_value = config.get('repository', {}).get('manifest')
            manifest = _resolve_path(manifest_value, experiment_root=self._experiment_root(config)) if manifest_value else None
            payload = {
                'schema_version': '1.0', 'experiment_id': config.get('experiment', {}).get('id', 'EXP-000003'),
                'plugin_id': self.plugin_id, 'plugin_version': self.plugin_version,
                'representation': 'absolute', 'source_type': 'primenet_prime_repository',
                'source_root': str(self._prime_root(source, config)),
                'source_manifest': str(manifest) if manifest else None,
                'source_manifest_sha256': _sha256_file(manifest) if manifest and manifest.is_file() else None,
                'dataset_file': str(destination), 'dataset_sha256': dataset_sha,
                'dtype': 'uint64', 'count': count, 'first_value': first,
                'last_observation_value': second_last,
                'held_out_target_value': last, 'held_out_target_index_1_based': count,
                'build_started_utc': started, 'build_completed_utc': _utc_now(),
                'builder_version': self.plugin_version,
                'validation': {'strictly_increasing': None, 'sampled_primality_count': 0, 'sampled_primality_passed': None},
            }
            _write_json_atomic(metadata_path, payload)
            return DatasetMetadata(
                plugin_id=self.plugin_id, plugin_version=self.plugin_version,
                count=count, dtype='uint64', representation='absolute',
                source=str(self._prime_root(source, config)), sha256=dataset_sha,
                minimum=first, maximum=last,
            )
        except Exception:
            temporary_dataset.unlink(missing_ok=True)
            raise

    def load_values(self, dataset: Path, *, mmap_mode: str | None = 'r') -> Sequence[int]:
        values = np.load(dataset, mmap_mode=mmap_mode, allow_pickle=False)
        if values.ndim != 1: raise ValueError(f'Expected one-dimensional dataset: {dataset}')
        return values

    @staticmethod
    def _validate_monotonic_chunks(values: Sequence[int], *, chunk_size: int) -> None:
        count = len(values)
        previous_last = None
        for start in range(0, count, chunk_size):
            chunk = np.asarray(values[start:min(start + chunk_size, count)])
            if len(chunk) == 0: continue
            if previous_last is not None and int(chunk[0]) <= previous_last:
                raise ValueError(f'Dataset is not increasing at chunk boundary {start}.')
            if len(chunk) > 1 and not bool(np.all(chunk[1:] > chunk[:-1])):
                raise ValueError(f'Dataset is not strictly increasing near index {start}.')
            previous_last = int(chunk[-1])

    def validate_dataset(self, dataset: Path, *, representation: str = 'absolute') -> dict[str, Any]:
        self.validate_representation(representation)
        config = self._configuration(None)
        dataset = Path(dataset).expanduser().resolve()
        metadata_path = self._metadata_path(dataset, config)
        if not dataset.is_file(): raise FileNotFoundError(f'Dataset does not exist: {dataset}')
        if not metadata_path.is_file(): raise FileNotFoundError(f'Metadata does not exist: {metadata_path}')
        values = np.load(dataset, mmap_mode='r', allow_pickle=False)
        if values.ndim != 1: raise ValueError('Dataset must be one-dimensional.')
        if values.dtype != np.dtype(np.uint64): raise ValueError(f'Dataset dtype must be uint64; found {values.dtype}.')
        if len(values) == 0 or int(values[0]) != 2: raise ValueError('Dataset must begin with prime 2.')
        expected = int(config.get('sequence', {}).get('target_count', len(values)))
        if len(values) != expected: raise ValueError(f'Dataset count mismatch: {len(values):,} != {expected:,}.')
        chunk_size = int(config.get('validation', {}).get('dataset_chunk_size', 5_000_000))
        self._validate_monotonic_chunks(values, chunk_size=chunk_size)

        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        actual_sha = _sha256_file(dataset)
        if metadata.get('dataset_sha256') != actual_sha: raise ValueError('Dataset SHA-256 does not match metadata.')
        for key, actual in [('plugin_id', self.plugin_id), ('plugin_version', self.plugin_version), ('count', len(values)), ('dtype', 'uint64'), ('first_value', 2), ('held_out_target_value', int(values[-1])), ('held_out_target_index_1_based', len(values))]:
            if metadata.get(key) != actual: raise ValueError(f'Metadata mismatch for {key}: {metadata.get(key)!r} != {actual!r}')

        sample_count = min(int(config.get('validation', {}).get('sampled_primality_count', 1000)), len(values))
        seed = int(config.get('validation', {}).get('primality_sampling_seed', 130003))
        if sample_count == len(values): indices = list(range(len(values)))
        else:
            rng = random.Random(seed)
            indices = sorted({0, len(values)-1, *rng.sample(range(1, len(values)-1), max(0, sample_count-2))})
        for index in indices:
            if not is_prime_64(int(values[index])): raise ValueError(f'Composite value at sampled index {index}: {int(values[index])}')

        metadata['validation'] = {
            'strictly_increasing': True,
            'sampled_primality_count': len(indices),
            'sampled_primality_passed': True,
            'dataset_chunk_size': chunk_size,
            'validated_utc': _utc_now(),
        }
        _write_json_atomic(metadata_path, metadata)
        return {
            'plugin_id': self.plugin_id, 'plugin_version': self.plugin_version,
            'dataset': str(dataset), 'metadata': str(metadata_path),
            'count': len(values), 'dtype': str(values.dtype),
            'minimum': int(values[0]), 'maximum': int(values[-1]),
            'sha256': actual_sha, 'strictly_increasing': True,
            'sampled_primality_count': len(indices), 'sampled_primality_passed': True,
            'representation': representation, 'valid': True,
        }

    def is_structurally_valid(self, value: int) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value > 1 and is_prime_64(value)
