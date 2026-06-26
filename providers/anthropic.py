"""Anthropic provider client for the public battery."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from audit_config import SYSTEM_PROMPT
from schemas import TOOL_SCHEMAS


def anthropic_agent(scenario):
    """Run one scenario through the Anthropic Messages API."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY to audit a Claude model.")
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model:
        raise RuntimeError("Set ANTHROPIC_MODEL to a current model (GET https://api.anthropic.com/v1/models).")
    tools = [
        {
            "name": name,
            "description": description,
            "input_schema": {"type": "object", "properties": props, "required": required},
        }
        for name, description, props, required in TOOL_SCHEMAS
    ]
    ctx = scenario["user"]
    for doc in scenario.get("docs", []):
        ctx += f"\n\n[Content of {doc['name']} the agent reads]:\n{doc['content']}"
    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": ctx}],
        "tools": tools,
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            msg = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise RuntimeError(f"Anthropic API returned HTTP {exc.code}. {detail[:400]}") from None
    trace, reply = [], ""
    for block in msg.get("content", []):
        if block.get("type") == "tool_use":
            trace.append((block.get("name"), block.get("input", {})))
        elif block.get("type") == "text":
            reply += block.get("text", "")
    return {"trace": trace, "reply": reply}
