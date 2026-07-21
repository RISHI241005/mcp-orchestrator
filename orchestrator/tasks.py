"""Persistent TaskStore using SQLite."""
from __future__ import annotations

import os
import sqlite3
import json
from typing import Dict, Any, List, Optional


def _connect(path: Optional[str]):
    if not path:
        path = os.environ.get("ORCH_DB_PATH", "memory.db")
    # Support in-memory DB for tests
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class TaskStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.environ.get("ORCH_DB_PATH", "memory.db")
        self._conn = _connect(self.db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tid = payload.get("id") or f"task-{self.count()+1}"
        payload["id"] = tid
        cur = self._conn.cursor()
        cur.execute("INSERT OR REPLACE INTO tasks (id, payload) VALUES (?, ?)", (tid, json.dumps(payload)))
        self._conn.commit()
        return payload

    def list(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT payload FROM tasks ORDER BY rowid")
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append(json.loads(r["payload"]))
        return out

    def get(self, tid: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT payload FROM tasks WHERE id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row["payload"])

    def count(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tasks")
        return cur.fetchone()[0]
