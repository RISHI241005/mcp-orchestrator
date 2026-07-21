"""API key management with roles and simple persistence.

Supports loading keys from ORCH_API_KEYS env var (JSON: {"key":"role", ...}) and runtime keys stored in MemoryStore under 'api_keys'.
"""
from __future__ import annotations

import os
import json
from typing import Optional, Dict
from orchestrator.memory import MemoryStore

memory = MemoryStore()


def _load_env_keys() -> Dict[str, str]:
    raw = os.environ.get("ORCH_API_KEYS")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        # support semicolon-separated key:role pairs like key1:admin;key2:user
        parts = [p for p in raw.split(";") if p.strip()]
        out = {}
        for p in parts:
            if ":" in p:
                k, r = p.split(":", 1)
                out[k.strip()] = r.strip()
        return out
    return {}


def get_all_keys() -> Dict[str, str]:
    env_keys = _load_env_keys()
    stored = memory.get("api_keys", {}) or {}
    # stored keys override env keys
    combined = {**env_keys, **stored}
    return combined


def check_key_role(key: str) -> Optional[str]:
    if not key:
        return None
    keys = get_all_keys()
    return keys.get(key)


def add_key(key: str, role: str = "user") -> None:
    keys = memory.get("api_keys", {}) or {}
    keys[key] = role
    memory.set("api_keys", keys)


def remove_key(key: str) -> None:
    keys = memory.get("api_keys", {}) or {}
    if key in keys:
        keys.pop(key)
        memory.set("api_keys", keys)
