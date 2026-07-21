"""FastAPI endpoints for MCP Orchestrator (minimal).

Provides a health endpoint and a simple search endpoint that delegates to MCPClient.
"""
from fastapi import FastAPI, HTTPException
from orchestrator.mcp_client import MCPClient

app = FastAPI(title="MCP Orchestrator API")
client = MCPClient()


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
