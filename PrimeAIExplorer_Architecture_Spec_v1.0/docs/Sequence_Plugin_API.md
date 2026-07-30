# Sequence Plugin API

## Required metadata

```python
plugin_id: str
display_name: str
definition: str
plugin_version: str
supported_representations: tuple[str, ...]
```

## Required methods

```python
validate_source() -> ValidationReport
build_dataset(request: DatasetBuildRequest) -> DatasetArtifact
validate_dataset(path: Path) -> ValidationReport
load_dataset(path: Path) -> Sequence[int]
make_window(request: WindowRequest) -> SequenceWindow
structural_validity(value: int) -> bool | None
metadata() -> dict
```

## Required guarantees

- Dataset order is canonical.
- Indices use an explicitly documented base.
- Dataset dtype is documented.
- Build operations are atomic.
- Existing datasets are protected unless overwrite is explicit.
- Source repository files remain read-only.
- Structural validity is deterministic for the supported numeric range.

## Reference plugin identifiers

```text
prime_gap
left_twin
right_twin
twin_gap
prime_constellation
custom_sequence
```

## Canonical `SequenceWindow`

```json
{
  "endpoint_index_1_based": 100000000,
  "target_index_1_based": 100000001,
  "window_size": 64,
  "representation": "combined",
  "observed": [12, 30, 18],
  "current_value": 123456789,
  "target_value": 123456831
}
```

The target value is private and must never be included in public cases.
