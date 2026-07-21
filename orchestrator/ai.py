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
        "Authorization": f"Bearer {api_key}",
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
