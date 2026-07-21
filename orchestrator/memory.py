"""Persistent memory layer using SQLite for simple key/value storage."""
from __future__ import annotations

import os
import sqlite3
import json
from typing import Any, Optional, Dict

# Optional MySQL support
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


def _connect_mysql():
    host = os.environ.get("ORCH_DB_HOST", "localhost")
    port = int(os.environ.get("ORCH_DB_PORT", "3306"))
    user = os.environ.get("ORCH_DB_USER", "root")
    password = os.environ.get("ORCH_DB_PASS", "")
    db = os.environ.get("ORCH_DB_NAME", "mcp_orchestrator")
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, autocommit=True)
    return conn


class MemoryStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.is_mysql = _use_mysql() and pymysql is not None
        if self.is_mysql:
            self._conn = _connect_mysql()
        else:
            self.path = path or os.environ.get("ORCH_DB_PATH", "memory.db")
            self._conn = _connect_sqlite(self.path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    `key` VARCHAR(191) PRIMARY KEY,
                    `value` LONGTEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
        if not self.is_mysql:
            self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("SELECT value FROM memory WHERE `key` = %s", (key,))
            row = cur.fetchone()
            if not row:
                return default
            try:
                return json.loads(row[0])
            except Exception:
                return row[0]
        else:
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
        if self.is_mysql:
            cur.execute("REPLACE INTO memory (`key`, `value`) VALUES (%s, %s)", (key, json.dumps(value)))
        else:
            cur.execute("INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            self._conn.commit()

    def all(self) -> Dict[str, Any]:
        cur = self._conn.cursor()
        if self.is_mysql:
            cur.execute("SELECT `key`, `value` FROM memory")
            rows = cur.fetchall()
            out = {}
            for r in rows:
                try:
                    out[r[0]] = json.loads(r[1])
                except Exception:
                    out[r[0]] = r[1]
            return out
        else:
            cur.execute("SELECT key, value FROM memory")
            rows = cur.fetchall()
            out = {}
            for r in rows:
                try:
                    out[r["key"]] = json.loads(r["value"])
                except Exception:
                    out[r["key"]] = r["value"]
            return out
