"""SQLite-backed persistent experiment catalog."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import CatalogRecord, SearchQuery


_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS catalog_records (
    record_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    dataset_id TEXT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    sequence_type TEXT,
    case_count INTEGER,
    completed_case_count INTEGER,
    failed_case_count INTEGER,
    accuracy REAL,
    mean_absolute_error REAL,
    report_path TEXT,
    created_at_utc TEXT,
    started_at_utc TEXT,
    completed_at_utc TEXT,
    snapshot_sha256 TEXT NOT NULL UNIQUE,
    snapshot_json TEXT NOT NULL,
    registered_at_utc TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    )
);

CREATE INDEX IF NOT EXISTS idx_catalog_experiment
    ON catalog_records(experiment_id);
CREATE INDEX IF NOT EXISTS idx_catalog_dataset
    ON catalog_records(dataset_id);
CREATE INDEX IF NOT EXISTS idx_catalog_provider_model
    ON catalog_records(provider, model);
CREATE INDEX IF NOT EXISTS idx_catalog_status
    ON catalog_records(status);
CREATE INDEX IF NOT EXISTS idx_catalog_accuracy
    ON catalog_records(accuracy);
"""


class ExperimentCatalog:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def register(self, record: CatalogRecord) -> bool:
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT snapshot_sha256
                FROM catalog_records
                WHERE record_id = ?
                """,
                (record.record_id,),
            ).fetchone()

            if existing is not None:
                if existing["snapshot_sha256"] != record.snapshot_sha256:
                    raise RuntimeError(
                        "record_id already exists with different snapshot."
                    )
                return False

            connection.execute(
                """
                INSERT INTO catalog_records (
                    record_id,
                    experiment_id,
                    dataset_id,
                    name,
                    status,
                    provider,
                    model,
                    sequence_type,
                    case_count,
                    completed_case_count,
                    failed_case_count,
                    accuracy,
                    mean_absolute_error,
                    report_path,
                    created_at_utc,
                    started_at_utc,
                    completed_at_utc,
                    snapshot_sha256,
                    snapshot_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.experiment_id,
                    record.dataset_id,
                    record.name,
                    record.status,
                    record.provider,
                    record.model,
                    record.sequence_type,
                    record.case_count,
                    record.completed_case_count,
                    record.failed_case_count,
                    record.accuracy,
                    record.mean_absolute_error,
                    record.report_path,
                    record.created_at_utc,
                    record.started_at_utc,
                    record.completed_at_utc,
                    record.snapshot_sha256,
                    json.dumps(
                        record.snapshot,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                ),
            )
            return True

    def get(self, record_id: str) -> CatalogRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM catalog_records
                WHERE record_id = ?
                """,
                (record_id,),
            ).fetchone()

        if row is None:
            raise KeyError(record_id)
        return _record_from_row(row)

    def latest_for_experiment(
        self,
        experiment_id: str,
    ) -> CatalogRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM catalog_records
                WHERE experiment_id = ?
                ORDER BY
                    COALESCE(completed_at_utc, started_at_utc, created_at_utc, registered_at_utc)
                    DESC,
                    registered_at_utc DESC
                LIMIT 1
                """,
                (experiment_id,),
            ).fetchone()

        return _record_from_row(row) if row is not None else None

    def history(self, experiment_id: str) -> list[CatalogRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM catalog_records
                WHERE experiment_id = ?
                ORDER BY registered_at_utc, record_id
                """,
                (experiment_id,),
            ).fetchall()

        return [_record_from_row(row) for row in rows]

    def search(self, query: SearchQuery) -> list[CatalogRecord]:
        clauses = []
        parameters: list[object] = []

        for column, value in (
            ("experiment_id", query.experiment_id),
            ("dataset_id", query.dataset_id),
            ("provider", query.provider),
            ("model", query.model),
            ("status", query.status),
            ("sequence_type", query.sequence_type),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)

        if query.min_accuracy is not None:
            clauses.append("accuracy >= ?")
            parameters.append(query.min_accuracy)

        if query.max_accuracy is not None:
            clauses.append("accuracy <= ?")
            parameters.append(query.max_accuracy)

        if query.text is not None:
            clauses.append(
                "(name LIKE ? OR experiment_id LIKE ? OR model LIKE ? OR provider LIKE ?)"
            )
            pattern = f"%{query.text}%"
            parameters.extend([pattern, pattern, pattern, pattern])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.extend([query.limit, query.offset])

        sql = f"""
            SELECT *
            FROM catalog_records
            {where}
            ORDER BY
                COALESCE(completed_at_utc, started_at_utc, created_at_utc, registered_at_utc)
                DESC,
                experiment_id,
                record_id
            LIMIT ? OFFSET ?
        """

        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        return [_record_from_row(row) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            value = connection.execute(
                "SELECT COUNT(*) FROM catalog_records"
            ).fetchone()[0]
        return int(value)

    def export_jsonl(
        self,
        path: str | Path,
        records: Iterable[CatalogRecord] | None = None,
    ) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if records is None:
            records = self.search(SearchQuery(limit=1_000_000))

        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(
                    json.dumps(
                        record.to_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                )
        return destination

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _record_from_row(row: sqlite3.Row) -> CatalogRecord:
    return CatalogRecord(
        record_id=row["record_id"],
        experiment_id=row["experiment_id"],
        dataset_id=row["dataset_id"],
        name=row["name"],
        status=row["status"],
        provider=row["provider"],
        model=row["model"],
        sequence_type=row["sequence_type"],
        case_count=row["case_count"],
        completed_case_count=row["completed_case_count"],
        failed_case_count=row["failed_case_count"],
        accuracy=row["accuracy"],
        mean_absolute_error=row["mean_absolute_error"],
        report_path=row["report_path"],
        created_at_utc=row["created_at_utc"],
        started_at_utc=row["started_at_utc"],
        completed_at_utc=row["completed_at_utc"],
        snapshot_sha256=row["snapshot_sha256"],
        snapshot=json.loads(row["snapshot_json"]),
    )
