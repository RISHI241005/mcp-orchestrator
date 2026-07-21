"""FastAPI endpoints for MCP Orchestrator (minimal).

Provides a health endpoint and a simple search endpoint that delegates to MCPClient.
"""
import os
from fastapi import FastAPI, HTTPException, Body, Depends, Header
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

# API key auth: set ORCH_API_KEY to enable; if unset, endpoints are open for local dev
API_KEY = os.environ.get("ORCH_API_KEY")

def verify_api_key(x_api_key: str | None = Header(None)):
    if not API_KEY:
        return True
    if x_api_key == API_KEY:
        return True
    raise HTTPException(status_code=401, detail="Invalid API Key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
def search(q: str):
    try:
        res = client.search_restaurants(q)
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Admin endpoints (protected by API key)
@app.get("/admin/tasks")
def admin_list_tasks(authorized: bool = Depends(verify_api_key)):
    """Return all tasks in the DB for debugging/admins."""
    return tasks.list()


@app.get("/admin/memory")
def admin_memory(authorized: bool = Depends(verify_api_key)):
    """Return full memory store for debugging/admins."""
    return memory.all()


@app.post("/tasks")
def create_task(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(verify_api_key)):
    task = tasks.create(payload)
    return task


@app.get("/tasks")
def list_tasks(authorized: bool = Depends(verify_api_key)):
    return tasks.list()


@app.post("/prioritize")
def prioritize(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(verify_api_key)):
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
def route(task: Dict[str, Any] = Body(...), authorized: bool = Depends(verify_api_key)):
    try:
        target = router.route(task)
        return {"server": target}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/order")
def place_order(payload: Dict[str, Any] = Body(...), authorized: bool = Depends(verify_api_key)):
    """Accepts {"server": "food", ...order...} or bare order JSON (defaults server to 'food')."""
    try:
        server = payload.get("server", "food")
        # If client expects just order dictionary, send payload without server key
        order = {k: v for k, v in payload.items() if k != "server"}
        res = client.request(server, path="order", method="POST", json=order)
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
