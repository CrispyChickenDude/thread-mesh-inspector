"""SQLite history database — records topology events and per-node trends."""
from __future__ import annotations
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    source_name TEXT,
    node_extaddr TEXT,
    node_name   TEXT,
    description TEXT,
    severity    TEXT DEFAULT 'info',
    detail_json TEXT
);

CREATE TABLE IF NOT EXISTS node_metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    node_extaddr TEXT NOT NULL,
    source_name TEXT,
    rssi        INTEGER,
    lq_in       INTEGER,
    role        TEXT,
    parent_extaddr TEXT,
    is_stale    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dataset_fingerprints (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    source_name  TEXT NOT NULL,
    fingerprint  TEXT,
    network_name TEXT,
    channel      INTEGER
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_extaddr   ON events(node_extaddr);
CREATE INDEX IF NOT EXISTS idx_metrics_extaddr  ON node_metrics(node_extaddr);
CREATE INDEX IF NOT EXISTS idx_metrics_ts       ON node_metrics(timestamp);
"""


class HistoryDb:
    """
    Async SQLite wrapper for Thread mesh history.

    Step 5: full implementation. For now the schema is created and
    basic insert/query methods are stubbed.
    """

    def __init__(self, data_dir: str = "/data"):
        self._db_path = os.path.join(data_dir, "history.db")
        self._db = None

    async def open(self) -> None:
        try:
            import aiosqlite
            self._db = await aiosqlite.connect(self._db_path)
            await self._db.executescript(DB_SCHEMA)
            await self._db.commit()
            logger.info("History DB opened: %s", self._db_path)
        except ImportError:
            logger.warning("aiosqlite not installed — history will not be persisted.")
        except Exception as e:
            logger.error("Could not open history DB: %s", e)

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def record_event(self, kind: str, timestamp: datetime,
                           source_name: str = "", node_extaddr: str = "",
                           node_name: str = "", description: str = "",
                           severity: str = "info", detail: Optional[dict] = None) -> None:
        """Insert a mesh event into the history database."""
        if not self._db:
            return
        import json
        try:
            await self._db.execute(
                "INSERT INTO events (kind, timestamp, source_name, node_extaddr, node_name, "
                "description, severity, detail_json) VALUES (?,?,?,?,?,?,?,?)",
                (kind, timestamp.isoformat(), source_name, node_extaddr, node_name,
                 description, severity, json.dumps(detail) if detail else None)
            )
            await self._db.commit()
        except Exception as e:
            logger.error("Failed to record event: %s", e)

    async def record_node_metric(self, timestamp: datetime, node_extaddr: str,
                                 source_name: str = "", rssi: Optional[int] = None,
                                 lq_in: Optional[int] = None, role: str = "",
                                 parent_extaddr: str = "", is_stale: bool = False) -> None:
        """Insert a node metric snapshot into the history database."""
        if not self._db:
            return
        try:
            await self._db.execute(
                "INSERT INTO node_metrics (timestamp, node_extaddr, source_name, rssi, "
                "lq_in, role, parent_extaddr, is_stale) VALUES (?,?,?,?,?,?,?,?)",
                (timestamp.isoformat(), node_extaddr, source_name, rssi,
                 lq_in, role, parent_extaddr, int(is_stale))
            )
            await self._db.commit()
        except Exception as e:
            logger.error("Failed to record node metric: %s", e)

    async def get_recent_events(self, limit: int = 100,
                                node_extaddr: Optional[str] = None) -> list[dict]:
        """Fetch recent events, optionally filtered by node."""
        if not self._db:
            return []
        try:
            if node_extaddr:
                cursor = await self._db.execute(
                    "SELECT * FROM events WHERE node_extaddr=? ORDER BY timestamp DESC LIMIT ?",
                    (node_extaddr, limit)
                )
            else:
                cursor = await self._db.execute(
                    "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
                )
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in await cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to query events: %s", e)
            return []

    async def get_node_metrics(self, node_extaddr: str, limit: int = 500) -> list[dict]:
        """Fetch metric history for a single node (for trend charts)."""
        if not self._db:
            return []
        try:
            cursor = await self._db.execute(
                "SELECT timestamp, rssi, lq_in, role, parent_extaddr FROM node_metrics "
                "WHERE node_extaddr=? ORDER BY timestamp DESC LIMIT ?",
                (node_extaddr, limit)
            )
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in await cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to query metrics: %s", e)
            return []
