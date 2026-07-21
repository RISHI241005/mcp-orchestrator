import os
import json
import requests
from typing import Any, Dict


def _mock_prioritize(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # Simple deterministic fallback when no API key is configured
    from orchestrator.prioritizer import Prioritizer
    p = Prioritizer()
    score = p.score(task, context)
    return {"score": score, "mock": True, "reason": "local heuristic fallback"}


def llm_prioritize(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenAI Chat Completions to get a priority score for a task.

    Returns a dict like {"score": 0-100, "reason": "..."} or the mock fallback when OPENAI_API_KEY is unset.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("ORCH_AI_MODEL", "gpt-3.5-turbo")
    if not api_key:
        return _mock_prioritize(task, context)

    system = (
        "You are a helpful assistant that rates the priority of tasks. "
        "Given a JSON task and optional context, reply with a JSON object: {\"score\": <number 0-100>, \"reason\": \"short explanation\"}. "
        "Only emit valid JSON in the reply."
    )

    user_msg = {
        "task": task,
        "context": context
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_msg)}
        ],
        "temperature": 0.2,
        "max_tokens": 200
    }

    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Extract assistant content
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        return {"error": "unexpected response from LLM", "raw": data}

    # Try to parse JSON from content
    try:
        parsed = json.loads(content)
        # ensure score exists and is numeric
        if isinstance(parsed.get("score"), (int, float)):
            parsed["mock"] = False
            return parsed
    except Exception:
        # not strict JSON — attempt heuristic extraction
        pass

    # Heuristic: find first number in content and treat as score
    import re
    m = re.search(r"(\d{1,3})(?:\.|\s|$)", content)
    if m:
        try:
            val = int(m.group(1))
            val = max(0, min(100, val))
            return {"score": val, "reason": content.strip(), "mock": False}
        except Exception:
            pass

    return {"error": "could not parse LLM response", "content": content}


# --- New: LLM parse order and place order (mock-friendly) ---

def llm_parse_order(nl: str) -> Dict[str, Any]:
    """Parse a natural-language order into a structured order dict using the LLM when available.

    Returns {'items':[{'name':..., 'qty':N}], 'address':..., 'notes':...}
    Falls back to a simple regex-based parser when OPENAI_API_KEY is unset.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("ORCH_AI_MODEL", "gpt-3.5-turbo")
    if not api_key:
        # naive fallback: split by 'and' and look for quantities
        parts = [p.strip() for p in nl.split(' and ')]
        items = []
        import re
        for p in parts:
            m = re.match(r"(?:(\d+) )?(.*)", p)
            qty = int(m.group(1)) if m and m.group(1) else 1
            name = m.group(2).strip() if m and m.group(2) else p
            items.append({"name": name, "qty": qty})
        return {"items": items, "address": None, "notes": None, "mock": True}

    system = (
        "You are an assistant that extracts structured orders from a user's natural-language request. "
        "Given a short order sentence, respond ONLY with JSON like: {\"items\": [{\"name\": \"paneer butter masala\", \"qty\": 1}], \"address\": \"...\", \"notes\": \"...\"}. "
        "Do not include any other text."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": nl}
        ],
        "temperature": 0.0,
        "max_tokens": 200
    }
    headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}", "Content-Type": "application/json"}
    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["mock"] = False
        return parsed
    except Exception:
        # best-effort fallback
        return {"items": [{"name": nl, "qty": 1}], "address": None, "notes": None, "mock": False, "raw": data}


def place_order_via_mcp(client, order: Dict[str, Any]) -> Dict[str, Any]:
    """Place an order using the provided MCPClient instance. Client may return mocked responses if not configured."""
    try:
        # The MCPClient.request implementation supports a 'order' path; if not, this will still work as a mock.
        resp = client.request('food', path='order', method='POST', json=order)
        return {"ok": True, "response": resp}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
