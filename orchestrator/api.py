"""FastAPI endpoints for MCP Orchestrator (minimal).

Provides a health endpoint and a simple search endpoint that delegates to MCPClient.
"""
import os
from fastapi import FastAPI, HTTPException, Body, Depends, Header
from fastapi.responses import RedirectResponse
from orchestrator.mcp_client import MCPClient
from orchestrator.prioritizer import Prioritizer
from orchestrator.memory import MemoryStore
from orchestrator.router import Router
from orchestrator.tasks import TaskStore
from typing import Dict, Any

app = FastAPI(title="MCP Orchestrator API")
client = MCPClient()
prioritizer = Prioritizer()
memory = MemoryStore()
router = Router()
tasks = TaskStore()

# Mount UI router
from orchestrator.ui import router as ui_router
app.include_router(ui_router)

# API key auth: set ORCH_API_KEY to enable; if unset, endpoints are open for local dev

from fastapi import Request

from orchestrator.auth import check_key_role, add_key, remove_key, get_all_keys, require_role


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to the interactive API docs for convenience."""
    return RedirectResponse(url="/docs")


@app.get("/search")
def search(q: str):
    try:
        res = client.search_restaurants(q)
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Admin endpoints (protected by API key roles)
@app.get("/admin/tasks")
def admin_list_tasks(authorized: bool = Depends(require_role('admin'))):
    """Return all tasks in the DB for debugging/admins."""
    return tasks.list()


@app.get("/admin/memory")
def admin_memory(authorized: bool = Depends(require_role('admin'))):
    """Return full memory store for debugging/admins."""
    return memory.all()


@app.post('/admin/keys')
def admin_create_key(payload: Dict[str, str] = Body(...), authorized: bool = Depends(require_role('admin'))):
    """Create a new API key with role. Payload: {"key": "thekey", "role": "user"} or generate on client."""
    key = payload.get('key')
    role = payload.get('role', 'user')
    if not key:
        raise HTTPException(status_code=400, detail='key required')
    add_key(key, role)
    return {'key': key, 'role': role}


@app.delete('/admin/keys/{key}')
def admin_delete_key(key: str, authorized: bool = Depends(require_role('admin'))):
    remove_key(key)
    return {'removed': key}


@app.post("/tasks")
def create_task(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(require_role('user'))):
    task = tasks.create(payload)
    return task


@app.get("/tasks")
def list_tasks(authorized: bool = Depends(require_role('user'))):
    return tasks.list()


@app.post("/prioritize")
def prioritize(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(require_role('user'))):
    """Accept a JSON body like {"task": {...}, "context": {...}} or a bare task object."""
    try:
        if "task" in payload:
            task = payload.get("task")
            context = payload.get("context", {})
        else:
            task = payload
            context = {}
        score = prioritizer.score(task, context)
        return {"score": score}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/route")
def route(task: Dict[str, Any] = Body(...), authorized: bool = Depends(require_role('user'))):
    try:
        target = router.route(task)
        return {"server": target}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/order")
def place_order(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(require_role('user'))):
    """Accepts {"server": "food", ...order...} or bare order JSON (defaults server to 'food')."""
    try:
        server = payload.get("server", "food")
        # If client expects just order dictionary, send payload without server key
        order = {k: v for k, v in payload.items() if k != "server"}
        res = client.request(server, path="order", method="POST", json=order)
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
