"""OpenAI-compatible provider client for the public battery."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from audit_config import SYSTEM_PROMPT
from schemas import TOOL_SCHEMAS


def openai_agent(scenario):
    """Run one scenario through the OpenAI Chat Completions tool-calling API."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY to audit a real model.")
    tools = [
        {"type": "function", "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": props, "required": required},
        }}
        for name, description, props, required in TOOL_SCHEMAS
    ]
    ctx = scenario["user"]
    for doc in scenario.get("docs", []):
        ctx += f"\n\n[Content of {doc['name']} the agent reads]:\n{doc['content']}"
    payload = json.dumps({
        "model": os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ctx},
        ],
        "tools": tools,
    }).encode()  # no fixed temperature: GPT-5/o reasoning models reject non-default temperature
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(
        base + "/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            msg = json.load(response)["choices"][0]["message"]
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}. {detail[:400]}") from None
    trace = []
    for tool_call in msg.get("tool_calls") or []:
        try:
            args = json.loads(tool_call["function"].get("arguments") or "{}")
        except Exception:
            args = {}
        trace.append((tool_call["function"]["name"], args))
    return {"trace": trace, "reply": msg.get("content") or ""}
