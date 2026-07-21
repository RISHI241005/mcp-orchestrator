import os
import time
import secrets
import hashlib
import base64
import json
from typing import Dict, Any, Optional
import requests
from orchestrator.memory import MemoryStore

memory = MemoryStore()

AUTH_TOKEN_KEY = "swiggy_tokens"  # dict keyed by server name
PKCE_STORE_KEY = "swiggy_pkce"    # temporary store for verifiers and state


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def generate_pkce() -> Dict[str, str]:
    # code_verifier: high-entropy cryptographic random string
    code_verifier = secrets.token_urlsafe(64)
    code_verifier_bytes = code_verifier.encode("utf-8")
    code_challenge = _b64url_encode(hashlib.sha256(code_verifier_bytes).digest())
    return {"verifier": code_verifier, "challenge": code_challenge}


def build_authorize_url(server: str = "food", client_id: Optional[str] = None, redirect_uri: Optional[str] = None, scope: str = "mcp:tools") -> Dict[str, Any]:
    """Generate PKCE pair, store verifier+state, and return authorize URL and state.
    Uses ORCH_SWIGGY_AUTH_BASE (defaults to https://mcp.swiggy.com/auth/authorize) and client_id from env ORCH_SWIGGY_CLIENT_ID.
    """
    client_id = client_id or os.environ.get("ORCH_SWIGGY_CLIENT_ID")
    if not client_id:
        raise ValueError("Missing ORCH_SWIGGY_CLIENT_ID environment variable")
    redirect_uri = redirect_uri or os.environ.get("ORCH_SWIGGY_REDIRECT_URI", "http://localhost:8000/auth/callback")
    auth_base = os.environ.get("ORCH_SWIGGY_AUTH_BASE", "https://mcp.swiggy.com/auth/authorize")

    pkce = generate_pkce()
    state = secrets.token_urlsafe(32)

    # persist pkce data keyed by state
    store = memory.get(PKCE_STORE_KEY, {}) or {}
    store[state] = {"verifier": pkce["verifier"], "server": server, "created_at": int(time.time())}
    memory.set(PKCE_STORE_KEY, store)

    url = (
        f"{auth_base}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&code_challenge={pkce['challenge']}&code_challenge_method=S256&state={state}&scope={scope}"
    )
    return {"url": url, "state": state}


def exchange_code_for_token(code: str, state: str, server: str = "food", redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """Exchange authorization code for access token and store it in memory.

    Uses ORCH_SWIGGY_TOKEN_URL env or default to https://mcp.swiggy.com/auth/token
    """
    store = memory.get(PKCE_STORE_KEY, {}) or {}
    entry = store.get(state)
    if not entry:
        raise ValueError("Unknown or expired state")
    verifier = entry.get("verifier")
    # remove used state
    store.pop(state, None)
    memory.set(PKCE_STORE_KEY, store)

    redirect_uri = redirect_uri or os.environ.get("ORCH_SWIGGY_REDIRECT_URI", "http://localhost:8000/auth/callback")
    token_url = os.environ.get("ORCH_SWIGGY_TOKEN_URL", "https://mcp.swiggy.com/auth/token")

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": verifier,
        "redirect_uri": redirect_uri,
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(token_url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    access_token = data.get("access_token")
    expires_in = int(data.get("expires_in", 0))
    scope = data.get("scope")

    if not access_token:
        raise ValueError("Token exchange did not return access_token")

    tokens = memory.get(AUTH_TOKEN_KEY, {}) or {}
    tokens[server] = {
        "access_token": access_token,
        "scope": scope,
        "expires_at": int(time.time()) + expires_in if expires_in else None,
    }
    memory.set(AUTH_TOKEN_KEY, tokens)

    return {"server": server, "expires_in": expires_in, "scope": scope}


def get_token_for_server(server: str = "food") -> Optional[Dict[str, Any]]:
    tokens = memory.get(AUTH_TOKEN_KEY, {}) or {}
    return tokens.get(server)


def clear_token(server: str = "food") -> None:
    tokens = memory.get(AUTH_TOKEN_KEY, {}) or {}
    if server in tokens:
        tokens.pop(server)
        memory.set(AUTH_TOKEN_KEY, tokens)
