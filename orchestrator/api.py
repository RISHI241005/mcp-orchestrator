"""FastAPI endpoints for MCP Orchestrator (minimal).

Provides a health endpoint and a simple search endpoint that delegates to MCPClient.
"""
from fastapi import FastAPI, HTTPException, Body
from orchestrator.mcp_client import MCPClient
from orchestrator.prioritizer import Prioritizer
from orchestrator.memory import MemoryStore
from orchestrator.router import Router
from typing import Dict, Any

app = FastAPI(title="MCP Orchestrator API")
client = MCPClient()
prioritizer = Prioritizer()
memory = MemoryStore()
router = Router()

# Simple in-memory task store for demo purposes
_task_store: Dict[str, Dict[str, Any]] = {}


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


@app.post("/tasks")
def create_task(payload: Dict[str, Any] = Body(...)):
    tid = payload.get("id") or f"task-{len(_task_store)+1}"
    payload["id"] = tid
    _task_store[tid] = payload
    return payload


@app.get("/tasks")
def list_tasks():
    return list(_task_store.values())


@app.post("/prioritize")
def prioritize(payload: Dict[str, Any] = Body(...)):
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
def route(task: Dict[str, Any] = Body(...)):
    try:
        target = router.route(task)
        return {"server": target}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/order")
def place_order(payload: Dict[str, Any] = Body(...)):
    """Accepts {"server": "food", ...order...} or bare order JSON (defaults server to 'food')."""
    try:
        server = payload.get("server", "food")
        # If client expects just order dictionary, send payload without server key
        order = {k: v for k, v in payload.items() if k != "server"}
        res = client.request(server, path="order", method="POST", json=order)
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
