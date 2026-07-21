"""Persistent TaskStore using SQLite."""
from __future__ import annotations

import os
import sqlite3
import json
from typing import Dict, Any, List, Optional

# Optional MySQL support via PyMySQL if ORCH_DB_HOST or ORCH_DB_URL is provided
try:
    import pymysql
except Exception:
    pymysql = None  # type: ignore


def _use_mysql() -> bool:
    return bool(os.environ.get("ORCH_DB_HOST") or os.environ.get("ORCH_DB_URL"))


def _connect_sqlite(path: Optional[str]):
    if not path:
        path = os.environ.get("ORCH_DB_PATH", "memory.db")
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_mysql() -> pymysql.connections.Connection:
    # Read connection details from env vars or ORCH_DB_URL
    host = os.environ.get("ORCH_DB_HOST", "localhost")
    port = int(os.environ.get("ORCH_DB_PORT", "3306"))
    user = os.environ.get("ORCH_DB_USER", "root")
    password = os.environ.get("ORCH_DB_PASS", "")
    db = os.environ.get("ORCH_DB_NAME", "mcp_orchestrator")
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, autocommit=True)
    return conn


class TaskStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.is_mysql = _use_mysql() and pymysql is not None
        if self.is_mysql:
            self._conn = _connect_mysql()
        else:
            self.db_path = db_path or os.environ.get("ORCH_DB_PATH", "memory.db")
            self._conn = _connect_sqlite(self.db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(255) PRIMARY KEY,
                    payload LONGTEXT NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
        if not self.is_mysql:
            self._conn.commit()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tid = payload.get("id") or f"task-{self.count()+1}"
        payload["id"] = tid
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("REPLACE INTO tasks (id, payload) VALUES (%s, %s)", (tid, json.dumps(payload)))
        else:
            cur.execute("INSERT OR REPLACE INTO tasks (id, payload) VALUES (?, ?)", (tid, json.dumps(payload)))
            self._conn.commit()
        return payload

    def list(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("SELECT payload FROM tasks ORDER BY id")
            rows = cur.fetchall()
            out = []
            for r in rows:
                # pymysql returns tuples
                out.append(json.loads(r[0]))
            return out
        else:
            cur.execute("SELECT payload FROM tasks ORDER BY rowid")
            rows = cur.fetchall()
            out = []
            for r in rows:
                out.append(json.loads(r["payload"]))
            return out

    def get(self, tid: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("SELECT payload FROM tasks WHERE id = %s", (tid,))
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(row[0])
        else:
            cur.execute("SELECT payload FROM tasks WHERE id = ?", (tid,))
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(row["payload"])

    def count(self) -> int:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("SELECT COUNT(*) as c FROM tasks")
            return cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) as c FROM tasks")
            return cur.fetchone()[0]
