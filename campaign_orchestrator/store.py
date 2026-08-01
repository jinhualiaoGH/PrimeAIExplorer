"""SQLite lease, heartbeat, event, and stop-control store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from benchmark_campaign.models import CampaignWorkItem


_SCHEMA = """
CREATE TABLE IF NOT EXISTS orchestrator_leases (
    campaign_id TEXT NOT NULL,
    work_item_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    leased_at_utc TEXT NOT NULL,
    heartbeat_at_utc TEXT NOT NULL,
    lease_expires_at_utc TEXT NOT NULL,
    PRIMARY KEY (campaign_id, work_item_id)
);

CREATE TABLE IF NOT EXISTS orchestrator_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    work_item_id TEXT,
    worker_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_at_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orchestrator_events_campaign
    ON orchestrator_events(campaign_id, event_id);

CREATE TABLE IF NOT EXISTS orchestrator_controls (
    campaign_id TEXT PRIMARY KEY,
    stop_requested INTEGER NOT NULL DEFAULT 0,
    reason TEXT
);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class OrchestratorStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def acquire_lease(
        self,
        campaign_id: str,
        item: CampaignWorkItem,
        *,
        worker_id: str,
        lease_seconds: int,
    ) -> bool:
        now = utc_now()
        expires = now + timedelta(seconds=lease_seconds)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT lease_expires_at_utc
                FROM orchestrator_leases
                WHERE campaign_id = ?
                  AND work_item_id = ?
                """,
                (campaign_id, item.work_item_id),
            ).fetchone()

            if row is not None:
                current_expiry = datetime.fromisoformat(
                    row["lease_expires_at_utc"].replace(
                        "Z",
                        "+00:00",
                    )
                )
                if current_expiry > now:
                    return False
                connection.execute(
                    """
                    DELETE FROM orchestrator_leases
                    WHERE campaign_id = ?
                      AND work_item_id = ?
                    """,
                    (campaign_id, item.work_item_id),
                )

            connection.execute(
                """
                INSERT INTO orchestrator_leases (
                    campaign_id,
                    work_item_id,
                    worker_id,
                    leased_at_utc,
                    heartbeat_at_utc,
                    lease_expires_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    item.work_item_id,
                    worker_id,
                    utc_text(now),
                    utc_text(now),
                    utc_text(expires),
                ),
            )

        self.event(
            campaign_id,
            worker_id,
            "lease_acquired",
            item.work_item_id,
            {"lease_seconds": lease_seconds},
        )
        return True

    def heartbeat(
        self,
        campaign_id: str,
        work_item_id: str,
        *,
        worker_id: str,
        lease_seconds: int,
    ) -> bool:
        now = utc_now()
        expires = now + timedelta(seconds=lease_seconds)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE orchestrator_leases
                SET heartbeat_at_utc = ?,
                    lease_expires_at_utc = ?
                WHERE campaign_id = ?
                  AND work_item_id = ?
                  AND worker_id = ?
                """,
                (
                    utc_text(now),
                    utc_text(expires),
                    campaign_id,
                    work_item_id,
                    worker_id,
                ),
            )
            return cursor.rowcount == 1

    def release_lease(
        self,
        campaign_id: str,
        work_item_id: str,
        *,
        worker_id: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM orchestrator_leases
                WHERE campaign_id = ?
                  AND work_item_id = ?
                  AND worker_id = ?
                """,
                (campaign_id, work_item_id, worker_id),
            )

    def recover_expired(self, campaign_id: str) -> list[str]:
        now = utc_text(utc_now())
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT work_item_id, worker_id
                FROM orchestrator_leases
                WHERE campaign_id = ?
                  AND lease_expires_at_utc <= ?
                ORDER BY work_item_id
                """,
                (campaign_id, now),
            ).fetchall()
            connection.execute(
                """
                DELETE FROM orchestrator_leases
                WHERE campaign_id = ?
                  AND lease_expires_at_utc <= ?
                """,
                (campaign_id, now),
            )

        for row in rows:
            self.event(
                campaign_id,
                row["worker_id"],
                "lease_expired",
                row["work_item_id"],
                {},
            )
        return [str(row["work_item_id"]) for row in rows]

    def request_stop(
        self,
        campaign_id: str,
        *,
        reason: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orchestrator_controls (
                    campaign_id,
                    stop_requested,
                    reason
                )
                VALUES (?, 1, ?)
                ON CONFLICT(campaign_id) DO UPDATE SET
                    stop_requested = 1,
                    reason = excluded.reason
                """,
                (campaign_id, reason),
            )

    def clear_stop(self, campaign_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orchestrator_controls (
                    campaign_id,
                    stop_requested,
                    reason
                )
                VALUES (?, 0, NULL)
                ON CONFLICT(campaign_id) DO UPDATE SET
                    stop_requested = 0,
                    reason = NULL
                """,
                (campaign_id,),
            )

    def stop_state(
        self,
        campaign_id: str,
    ) -> tuple[bool, str | None]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT stop_requested, reason
                FROM orchestrator_controls
                WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchone()

        if row is None:
            return False, None
        return bool(row["stop_requested"]), row["reason"]

    def event(
        self,
        campaign_id: str,
        worker_id: str,
        event_type: str,
        work_item_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO orchestrator_events (
                    campaign_id,
                    work_item_id,
                    worker_id,
                    event_type,
                    event_at_utc,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    work_item_id,
                    worker_id,
                    event_type,
                    utc_text(utc_now()),
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )

    def list_events(
        self,
        campaign_id: str,
        *,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM orchestrator_events
                WHERE campaign_id = ?
                ORDER BY event_id
                LIMIT ?
                """,
                (campaign_id, limit),
            ).fetchall()

        return [
            {
                "event_id": row["event_id"],
                "campaign_id": row["campaign_id"],
                "work_item_id": row["work_item_id"],
                "worker_id": row["worker_id"],
                "event_type": row["event_type"],
                "event_at_utc": row["event_at_utc"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
