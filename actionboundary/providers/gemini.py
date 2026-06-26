"""Gemini provider client for the public battery."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..audit_config import SYSTEM_PROMPT
from ..schemas import TOOL_SCHEMAS


def gemini_agent(scenario):
    """Run one scenario through the Google Generative Language function-calling API."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY to audit a Gemini model.")
    model = os.environ.get("GEMINI_MODEL")
    if not model:
        raise RuntimeError("Set GEMINI_MODEL to a current model (GET .../v1beta/models?key=KEY).")
    decls = [
        {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": props, "required": required},
        }
        for name, description, props, required in TOOL_SCHEMAS
    ]
    ctx = scenario["user"]
    for doc in scenario.get("docs", []):
        ctx += f"\n\n[Content of {doc['name']} the agent reads]:\n{doc['content']}"
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": ctx}]}],
        "tools": [{"functionDeclarations": decls}],
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            msg = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}. {detail[:400]}") from None
    trace, reply = [], ""
    candidates = msg.get("candidates") or []
    if candidates:
        for part in candidates[0].get("content", {}).get("parts", []):
            if "functionCall" in part:
                function_call = part["functionCall"]
                trace.append((function_call.get("name"), function_call.get("args", {})))
            elif "text" in part:
                reply += part["text"]
    return {"trace": trace, "reply": reply}
