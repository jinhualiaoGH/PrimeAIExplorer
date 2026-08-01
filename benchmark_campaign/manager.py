"""Persistent, resumable benchmark campaign manager."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import (
    CampaignPlan,
    CampaignStatus,
    CampaignWorkItem,
)


_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    plan_sha256 TEXT NOT NULL,
    plan_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    )
);

CREATE TABLE IF NOT EXISTS campaign_work_items (
    campaign_id TEXT NOT NULL,
    work_item_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    dataset_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    random_seed INTEGER NOT NULL,
    window_size INTEGER NOT NULL,
    repeat_index INTEGER NOT NULL,
    model_parameters_json TEXT NOT NULL,
    status TEXT NOT NULL,
    experiment_id TEXT,
    catalog_record_id TEXT,
    attempts INTEGER NOT NULL,
    error_message TEXT,
    updated_at_utc TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    ),
    PRIMARY KEY (campaign_id, work_item_id),
    UNIQUE (campaign_id, ordinal),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_item_status
    ON campaign_work_items(campaign_id, status, ordinal);
CREATE INDEX IF NOT EXISTS idx_campaign_item_provider_model
    ON campaign_work_items(campaign_id, provider, model);
"""


class CampaignManager:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def create(self, plan: CampaignPlan) -> bool:
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT plan_sha256
                FROM campaigns
                WHERE campaign_id = ?
                """,
                (plan.campaign_id,),
            ).fetchone()

            if existing is not None:
                if existing["plan_sha256"] != plan.plan_sha256:
                    raise RuntimeError(
                        "campaign_id already exists with a different plan."
                    )
                return False

            connection.execute(
                """
                INSERT INTO campaigns (
                    campaign_id,
                    plan_sha256,
                    plan_json
                )
                VALUES (?, ?, ?)
                """,
                (
                    plan.campaign_id,
                    plan.plan_sha256,
                    json.dumps(
                        plan.to_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                ),
            )

            connection.executemany(
                """
                INSERT INTO campaign_work_items (
                    campaign_id,
                    work_item_id,
                    ordinal,
                    dataset_id,
                    provider,
                    model,
                    prompt_template,
                    random_seed,
                    window_size,
                    repeat_index,
                    model_parameters_json,
                    status,
                    experiment_id,
                    catalog_record_id,
                    attempts,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        plan.campaign_id,
                        item.work_item_id,
                        item.ordinal,
                        item.dataset_id,
                        item.provider,
                        item.model,
                        item.prompt_template,
                        item.random_seed,
                        item.window_size,
                        item.repeat_index,
                        json.dumps(
                            dict(item.model_parameters),
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False,
                        ),
                        item.status,
                        item.experiment_id,
                        item.catalog_record_id,
                        item.attempts,
                        item.error_message,
                    )
                    for item in plan.work_items
                ],
            )
        return True

    def status(self, campaign_id: str) -> CampaignStatus:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM campaign_work_items
                WHERE campaign_id = ?
                GROUP BY status
                """,
                (campaign_id,),
            ).fetchall()

            next_pending = connection.execute(
                """
                SELECT MIN(ordinal)
                FROM campaign_work_items
                WHERE campaign_id = ?
                  AND status = 'pending'
                """,
                (campaign_id,),
            ).fetchone()[0]

        counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }
        for row in rows:
            counts[row["status"]] = int(row["count"])

        total = sum(counts.values())
        terminal = (
            counts["completed"]
            + counts["failed"]
            + counts["skipped"]
        )

        return CampaignStatus(
            campaign_id=campaign_id,
            total=total,
            pending=counts["pending"],
            running=counts["running"],
            completed=counts["completed"],
            failed=counts["failed"],
            skipped=counts["skipped"],
            progress_fraction=(
                terminal / total if total else 0.0
            ),
            next_pending_ordinal=(
                int(next_pending)
                if next_pending is not None
                else None
            ),
        )

    def claim_next(
        self,
        campaign_id: str,
    ) -> CampaignWorkItem | None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT *
                FROM campaign_work_items
                WHERE campaign_id = ?
                  AND status = 'pending'
                ORDER BY ordinal
                LIMIT 1
                """,
                (campaign_id,),
            ).fetchone()

            if row is None:
                return None

            connection.execute(
                """
                UPDATE campaign_work_items
                SET status = 'running',
                    attempts = attempts + 1,
                    updated_at_utc = strftime(
                        '%Y-%m-%dT%H:%M:%fZ',
                        'now'
                    )
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (campaign_id, row["work_item_id"]),
            )

            updated = connection.execute(
                """
                SELECT *
                FROM campaign_work_items
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (campaign_id, row["work_item_id"]),
            ).fetchone()

        return _item_from_row(updated)

    def complete(
        self,
        campaign_id: str,
        work_item_id: str,
        *,
        experiment_id: str,
        catalog_record_id: str | None = None,
    ) -> CampaignWorkItem:
        return self._transition(
            campaign_id,
            work_item_id,
            status="completed",
            experiment_id=experiment_id,
            catalog_record_id=catalog_record_id,
            error_message=None,
        )

    def fail(
        self,
        campaign_id: str,
        work_item_id: str,
        *,
        error_message: str,
    ) -> CampaignWorkItem:
        return self._transition(
            campaign_id,
            work_item_id,
            status="failed",
            experiment_id=None,
            catalog_record_id=None,
            error_message=error_message,
        )

    def reset_failed(self, campaign_id: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE campaign_work_items
                SET status = 'pending',
                    error_message = NULL,
                    updated_at_utc = strftime(
                        '%Y-%m-%dT%H:%M:%fZ',
                        'now'
                    )
                WHERE campaign_id = ?
                  AND status = 'failed'
                """,
                (campaign_id,),
            )
            return int(cursor.rowcount)

    def list_items(
        self,
        campaign_id: str,
        *,
        status: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[CampaignWorkItem]:
        clauses = ["campaign_id = ?"]
        parameters: list[object] = [campaign_id]

        if status is not None:
            clauses.append("status = ?")
            parameters.append(status)

        parameters.extend([limit, offset])

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM campaign_work_items
                WHERE {' AND '.join(clauses)}
                ORDER BY ordinal
                LIMIT ? OFFSET ?
                """,
                parameters,
            ).fetchall()

        return [_item_from_row(row) for row in rows]

    def export_plan_jsonl(
        self,
        campaign_id: str,
        path: str | Path,
    ) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        items = self.list_items(
            campaign_id,
            limit=1_000_000,
        )

        with destination.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            for item in items:
                handle.write(
                    json.dumps(
                        item.to_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                )

        return destination

    def _transition(
        self,
        campaign_id: str,
        work_item_id: str,
        *,
        status: str,
        experiment_id: str | None,
        catalog_record_id: str | None,
        error_message: str | None,
    ) -> CampaignWorkItem:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT status
                FROM campaign_work_items
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (campaign_id, work_item_id),
            ).fetchone()

            if row is None:
                raise KeyError(work_item_id)

            if row["status"] != "running":
                raise RuntimeError(
                    "only running work items may transition."
                )

            connection.execute(
                """
                UPDATE campaign_work_items
                SET status = ?,
                    experiment_id = ?,
                    catalog_record_id = ?,
                    error_message = ?,
                    updated_at_utc = strftime(
                        '%Y-%m-%dT%H:%M:%fZ',
                        'now'
                    )
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (
                    status,
                    experiment_id,
                    catalog_record_id,
                    error_message,
                    campaign_id,
                    work_item_id,
                ),
            )

            updated = connection.execute(
                """
                SELECT *
                FROM campaign_work_items
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (campaign_id, work_item_id),
            ).fetchone()

        return _item_from_row(updated)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _item_from_row(row: sqlite3.Row) -> CampaignWorkItem:
    return CampaignWorkItem(
        work_item_id=row["work_item_id"],
        ordinal=row["ordinal"],
        dataset_id=row["dataset_id"],
        provider=row["provider"],
        model=row["model"],
        prompt_template=row["prompt_template"],
        random_seed=row["random_seed"],
        window_size=row["window_size"],
        repeat_index=row["repeat_index"],
        model_parameters=json.loads(
            row["model_parameters_json"]
        ),
        status=row["status"],
        experiment_id=row["experiment_id"],
        catalog_record_id=row["catalog_record_id"],
        attempts=row["attempts"],
        error_message=row["error_message"],
    )
