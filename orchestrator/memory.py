"""Persistent memory layer using SQLite for simple key/value storage."""
from __future__ import annotations

import os
import sqlite3
import json
from typing import Any, Optional, Dict


def _connect(path: Optional[str]):
    if not path:
        path = os.environ.get("ORCH_DB_PATH", "memory.db")
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class MemoryStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.environ.get("ORCH_DB_PATH", "memory.db")
        self._conn = _connect(self.path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM memory WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]

    def set(self, key: str, value) -> None:
        cur = self._conn.cursor()
        cur.execute("INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self._conn.commit()

    def all(self) -> Dict[str, Any]:
        cur = self._conn.cursor()
        cur.execute("SELECT key, value FROM memory")
        rows = cur.fetchall()
        out = {}
        for r in rows:
            try:
                out[r["key"]] = json.loads(r["value"])
            except Exception:
                out[r["key"]] = r["value"]
        return out
