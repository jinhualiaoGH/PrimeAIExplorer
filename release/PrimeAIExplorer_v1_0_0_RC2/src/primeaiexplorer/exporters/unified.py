"""Unified, deterministic export for PrimeAIExplorer observatory results."""
from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from primeaiexplorer.observatories import ObservatoryResult


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"value of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class UnifiedExportEngine:
    """Export all observatory results into one portable analysis package."""

    schema_version = "1.0.0"

    def export(
        self,
        results: Mapping[str, ObservatoryResult],
        output_dir: str | Path,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if not isinstance(results, Mapping) or not results:
            raise ValueError("results must be a non-empty mapping")
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        tables_dir = output / "tables"
        tables_dir.mkdir(exist_ok=True)
        context_dict = dict(context or {})

        serial: dict[str, Any] = {}
        metric_rows: list[dict[str, Any]] = []
        catalog_rows: list[dict[str, Any]] = []
        table_files: list[str] = []

        for name, result in results.items():
            if not isinstance(result, ObservatoryResult):
                raise TypeError(f"result {name!r} must be ObservatoryResult")
            if name != result.name:
                raise ValueError(f"result key {name!r} does not match result name {result.name!r}")
            serial[name] = result.to_dict()
            for metric, value in result.metrics.items():
                metric_rows.append({"observatory": name, "metric": metric, "value": value})
            catalog_rows.append({
                "name": name,
                "version": result.version,
                "metric_count": len(result.metrics),
                "table_count": len(result.tables),
                "warning_count": len(result.warnings),
            })
            for table_name, rows in result.tables.items():
                relative = Path("tables") / f"{name}__{table_name}.csv"
                self._write_table(output / relative, rows)
                table_files.append(relative.as_posix())

        summary = {
            "schema_version": self.schema_version,
            "observatory_count": len(serial),
            "metric_count": len(metric_rows),
            "table_count": len(table_files),
            "warning_count": sum(len(item.warnings) for item in results.values()),
            "observatories": list(serial),
            "context": context_dict,
        }
        _write_json(output / "summary.json", summary)
        _write_json(output / "observatories.json", serial)
        self._write_rows(output / "metrics.csv", metric_rows, ["observatory", "metric", "value"])
        self._write_rows(output / "observatory_catalog.csv", catalog_rows,
                         ["name", "version", "metric_count", "table_count", "warning_count"])

        artifacts = ["summary.json", "observatories.json", "metrics.csv", "observatory_catalog.csv", *table_files]
        manifest = {
            "schema_version": self.schema_version,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "context": context_dict,
            "artifacts": [
                {"path": rel, "sha256": _sha256(output / rel), "bytes": (output / rel).stat().st_size}
                for rel in artifacts
            ],
        }
        _write_json(output / "manifest.json", manifest)
        return {"output_dir": str(output), "summary": summary, "manifest": manifest}

    @staticmethod
    def _write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @classmethod
    def _write_table(cls, path: Path, rows: Any) -> None:
        normalized = [dict(row) for row in rows]
        fields: list[str] = []
        for row in normalized:
            for key in row:
                if key not in fields:
                    fields.append(key)
        cls._write_rows(path, normalized, fields or ["empty"])
