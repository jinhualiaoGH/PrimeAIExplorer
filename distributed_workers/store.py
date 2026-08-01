"""Persistent worker registry, heartbeats, controls, and D5 audit events."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS distributed_workers (
  campaign_id TEXT NOT NULL,
  worker_id TEXT NOT NULL,
  status TEXT NOT NULL,
  registered_at_utc TEXT NOT NULL,
  heartbeat_at_utc TEXT NOT NULL,
  stopped_at_utc TEXT,
  metadata_json TEXT NOT NULL,
  PRIMARY KEY (campaign_id, worker_id)
);
CREATE INDEX IF NOT EXISTS idx_distributed_workers_status
ON distributed_workers(campaign_id, status, heartbeat_at_utc);
CREATE TABLE IF NOT EXISTS distributed_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_id TEXT NOT NULL,
  worker_id TEXT,
  event_type TEXT NOT NULL,
  event_at_utc TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS distributed_controls (
  campaign_id TEXT PRIMARY KEY,
  paused INTEGER NOT NULL DEFAULT 0,
  reason TEXT
);
"""

def _now() -> datetime: return datetime.now(timezone.utc)
def _text(v: datetime) -> str: return v.isoformat().replace('+00:00','Z')

class WorkerStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as c: c.executescript(_SCHEMA)

    def register(self, campaign_id: str, worker_id: str, metadata: dict[str, Any] | None = None) -> None:
        now = _text(_now())
        payload = json.dumps(metadata or {}, sort_keys=True, separators=(',', ':'))
        with self._connect() as c:
            c.execute("""INSERT INTO distributed_workers
            (campaign_id,worker_id,status,registered_at_utc,heartbeat_at_utc,stopped_at_utc,metadata_json)
            VALUES (?,?, 'running', ?, ?, NULL, ?)
            ON CONFLICT(campaign_id,worker_id) DO UPDATE SET
              status='running', heartbeat_at_utc=excluded.heartbeat_at_utc,
              stopped_at_utc=NULL, metadata_json=excluded.metadata_json""",
              (campaign_id, worker_id, now, now, payload))
        self.event(campaign_id, worker_id, 'worker_registered', metadata or {})

    def heartbeat(self, campaign_id: str, worker_id: str) -> bool:
        with self._connect() as c:
            cur = c.execute("""UPDATE distributed_workers SET heartbeat_at_utc=?
            WHERE campaign_id=? AND worker_id=? AND status='running'""",
            (_text(_now()), campaign_id, worker_id))
            return cur.rowcount == 1

    def stop(self, campaign_id: str, worker_id: str, *, status: str='stopped') -> None:
        now = _text(_now())
        with self._connect() as c:
            c.execute("""UPDATE distributed_workers SET status=?, heartbeat_at_utc=?, stopped_at_utc=?
            WHERE campaign_id=? AND worker_id=?""", (status, now, now, campaign_id, worker_id))
        self.event(campaign_id, worker_id, 'worker_deregistered', {'status': status})

    def recover_stale(self, campaign_id: str, stale_after_seconds: float) -> list[str]:
        cutoff = _text(_now() - timedelta(seconds=stale_after_seconds))
        with self._connect() as c:
            c.execute('BEGIN IMMEDIATE')
            rows = c.execute("""SELECT worker_id FROM distributed_workers
            WHERE campaign_id=? AND status='running' AND heartbeat_at_utc<=?
            ORDER BY worker_id""", (campaign_id, cutoff)).fetchall()
            for row in rows:
                c.execute("""UPDATE distributed_workers SET status='stale', stopped_at_utc=?
                WHERE campaign_id=? AND worker_id=?""", (_text(_now()), campaign_id, row['worker_id']))
        result=[str(r['worker_id']) for r in rows]
        for worker_id in result: self.event(campaign_id, worker_id, 'worker_recovered_stale', {})
        return result

    def list_workers(self, campaign_id: str) -> list[dict[str, Any]]:
        with self._connect() as c:
            rows=c.execute("""SELECT * FROM distributed_workers WHERE campaign_id=? ORDER BY worker_id""",(campaign_id,)).fetchall()
        return [{**dict(r), 'metadata': json.loads(r['metadata_json'])} for r in rows]

    def pause(self, campaign_id: str, reason: str | None=None) -> None:
        with self._connect() as c:
            c.execute("""INSERT INTO distributed_controls(campaign_id,paused,reason) VALUES(?,1,?)
            ON CONFLICT(campaign_id) DO UPDATE SET paused=1, reason=excluded.reason""",(campaign_id,reason))
        self.event(campaign_id, None, 'campaign_paused', {'reason': reason})

    def resume(self, campaign_id: str) -> None:
        with self._connect() as c:
            c.execute("""INSERT INTO distributed_controls(campaign_id,paused,reason) VALUES(?,0,NULL)
            ON CONFLICT(campaign_id) DO UPDATE SET paused=0, reason=NULL""",(campaign_id,))
        self.event(campaign_id, None, 'campaign_resumed', {})

    def pause_state(self, campaign_id: str) -> tuple[bool, str | None]:
        with self._connect() as c:
            r=c.execute('SELECT paused,reason FROM distributed_controls WHERE campaign_id=?',(campaign_id,)).fetchone()
        return (False,None) if r is None else (bool(r['paused']), r['reason'])

    def event(self, campaign_id: str, worker_id: str | None, event_type: str, payload: dict[str, Any]) -> None:
        with self._connect() as c:
            c.execute("""INSERT INTO distributed_events(campaign_id,worker_id,event_type,event_at_utc,payload_json)
            VALUES(?,?,?,?,?)""",(campaign_id,worker_id,event_type,_text(_now()),json.dumps(payload,sort_keys=True,separators=(',',':'))))

    def list_events(self, campaign_id: str, limit: int=1000) -> list[dict[str, Any]]:
        with self._connect() as c:
            rows=c.execute("""SELECT * FROM distributed_events WHERE campaign_id=? ORDER BY event_id LIMIT ?""",(campaign_id,limit)).fetchall()
        return [{**dict(r), 'payload': json.loads(r['payload_json'])} for r in rows]

    def _connect(self) -> sqlite3.Connection:
        c=sqlite3.connect(self.database_path, timeout=30.0)
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA busy_timeout=30000')
        return c
