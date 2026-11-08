"""OrcaRouter Cyber Inference provider for the public battery.

OrcaRouter is an OpenAI-compatible AI gateway: one endpoint
(``https://api.orcarouter.ai/v1``) routes many providers, including the
OrcaCyber models published for authorized security work. Wire-format handling is
shared with the OpenAI client in ``actionboundary.providers.openai``; this module
only owns OrcaRouter's own naming, credential variable, model selection, and
model catalog so OrcaRouter stays a first-class named provider.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from ..audit_config import SYSTEM_PROMPT
from ..schemas import TOOL_SCHEMAS

PROVIDER_NAME = "OrcaRouter Cyber Inference"
ORCAROUTER_PROVIDER_NAME = PROVIDER_NAME  # explicit name for registry imports
DEFAULT_BASE_URL = "https://api.orcarouter.ai/v1"
KEY_ENV = "ORCAROUTER_API_KEY"
MODEL_ENV = "ORCAROUTER_MODEL"
BASE_URL_ENV = "ORCAROUTER_BASE_URL"

# Default route: automatic routing across OrcaRouter's catalog, usable with any key.
DEFAULT_MODEL = "orcarouter/auto"
# General-purpose fallback when a dedicated OrcaCyber model is not enabled.
FALLBACK_MODEL = "orcarouter/fusion"
# Dedicated cyber models for teams cleared for authorized security work
# (https://www.orcarouter.ai/models?tier=cyber). Shown as recommendations in
# discovery output; not selected automatically.
RECOMMENDED_CYBER_MODELS = ("orca/orcacyber-ultra-1.0", "orca/orcacyber-zero-1.5")

# Verified cold-start catalog, used only when GET /models is unavailable. These are
# reasoning / text chat models; per-request capability is never inferred from names.
COLD_START_MODELS = (
    {"id": "orcarouter/auto", "name": "OrcaRouter Auto", "reasoning": False},
    {"id": "orca/orcacyber-ultra-1.0", "name": "OrcaCyber Ultra 1.0", "reasoning": True},
    {"id": "orca/orcacyber-zero-1.5", "name": "OrcaCyber Zero 1.5", "reasoning": True},
    {"id": "orcarouter/fusion", "name": "OrcaRouter Fusion", "reasoning": False},
)

# The battery's chat-completions tool-calling request can only speak these endpoint types.
CHAT_ENDPOINT_TYPES = ("openai", "openai-response", "anthropic", "gemini")
# Named non-chat capabilities: a model that declares one of these is not a text chat model,
# even when its endpoint list says "openai".
NON_CHAT_CAPABILITY_TYPES = ("audio_speech", "audio_transcription", "images", "image-generation")


def _endpoint_capabilities(item: dict) -> list:
    capabilities = item.get("endpoint_capabilities")
    return capabilities if isinstance(capabilities, list) else []


MODEL_LIST_TIMEOUT = 30  # seconds
MODEL_LIST_MAX_BYTES = 2_000_000
MODEL_LIST_MAX_ITEMS = 500


def _is_loopback(parts) -> bool:
    return parts.hostname in ("localhost", "127.0.0.1", "::1")


def _require_safe_origin(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme == "https" and parts.hostname:
        return url
    if parts.scheme == "http" and _is_loopback(parts):
        return url
    raise RuntimeError(f"{BASE_URL_ENV} must be an https:// origin (http:// only for loopback).")


def base_url() -> str:
    """Inference (or model catalog) base URL.

    An explicit ORCAROUTER_BASE_URL wins over the public default. Plain traffic
    to a remote origin must use HTTPS; HTTP is accepted only for loopback test
    servers. The key is sent only to this configured origin, never to a derived
    host.
    """
    return _require_safe_origin((os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/"))


def api_key() -> str | None:
    return os.environ.get(KEY_ENV) or None


def selected_model() -> str:
    return os.environ.get(MODEL_ENV) or DEFAULT_MODEL


def _speaks_chat_completions(item: dict) -> bool:
    """Fail closed: keep a record only if its declared endpoints include a text chat type.

    A record that declares a speech/image capability (``audio_speech``, ``images``, ...)
    is not a text chat model; a record with no declared endpoint types is rejected.
    Capabilities are never inferred from the model name.
    """
    endpoint_types = item.get("supported_endpoint_types")
    if not isinstance(endpoint_types, list):
        return False
    if set(_endpoint_capabilities(item)) & set(NON_CHAT_CAPABILITY_TYPES):
        return False
    return bool(set(endpoint_types) & set(CHAT_ENDPOINT_TYPES))


def list_models_url() -> str:
    return base_url() + "/models?capability=chat"


def _chat_models(payload) -> list[dict]:
    """Keep text chat-completions records only, bounded and shape-checked."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise ValueError("OrcaRouter model catalog response has no 'data' list.")
    models, seen = [], set()
    for item in data[:MODEL_LIST_MAX_ITEMS]:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip() or model_id in seen:
            continue
        if not _speaks_chat_completions(item):
            continue
        name = item.get("name") if isinstance(item.get("name"), str) else model_id
        models.append({"id": model_id, "name": name, "reasoning": bool(item.get("reasoning"))})
        seen.add(model_id)
    if not models:
        raise ValueError("OrcaRouter model catalog listed no chat models.")
    return models


def list_models(key=None) -> dict:
    """Fetch the live OrcaRouter model catalog, falling back to the verified seed.

    Returns ``{"source": "live" | "fallback", "base_url": ..., "models": [...],
    "recommended": [...], "default": ..., "error": str | None}``. The API key is
    never included in the result or in error text.
    """
    key = key or api_key()
    if not key:
        raise RuntimeError(f"Set {KEY_ENV} to list OrcaRouter models.")
    result = {
        "source": "live",
        "base_url": base_url(),
        "models": [],
        "recommended": list(RECOMMENDED_CYBER_MODELS),
        "default": DEFAULT_MODEL,
        "error": None,
    }
    req = urllib.request.Request(list_models_url(), headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=MODEL_LIST_TIMEOUT) as response:
            raw = response.read(MODEL_LIST_MAX_BYTES + 1)
        if len(raw) > MODEL_LIST_MAX_BYTES:
            raise ValueError("OrcaRouter model catalog response exceeded the size bound.")
        result["models"] = _chat_models(json.loads(raw.decode("utf-8")))
        return result
    except urllib.error.HTTPError as exc:
        result["error"] = f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result["error"] = f"network error ({type(exc).__name__})"
    except (ValueError, RuntimeError) as exc:
        result["error"] = f"catalog error ({exc})"
    # Live discovery failed: keep the provider usable with the verified seed only.
    result["source"] = "fallback"
    result["models"] = [dict(m) for m in COLD_START_MODELS]
    return result


def orcarouter_agent(scenario):
    """Run one scenario through OrcaRouter's OpenAI-compatible chat-completions API."""
    key = api_key()
    if not key:
        raise RuntimeError(f"Set {KEY_ENV} to audit a model through {PROVIDER_NAME}.")
    tools = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {"type": "object", "properties": props, "required": required},
            },
        }
        for name, description, props, required in TOOL_SCHEMAS
    ]
    ctx = scenario["user"]
    for doc in scenario.get("docs", []):
        ctx += f"\n\n[Content of {doc['name']} the agent reads]:\n{doc['content']}"
    payload = json.dumps(
        {
            "model": selected_model(),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": ctx},
            ],
            "tools": tools,
        }
    ).encode()  # no fixed temperature: reasoning models reject non-default temperature
    req = urllib.request.Request(
        base_url() + "/chat/completions",
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
        except OSError:
            pass  # error body already consumed or connection dropped; status code is kept
        hint = f" Check {KEY_ENV} / {MODEL_ENV}." if exc.code in (401, 403, 404) else ""
        raise RuntimeError(f"{PROVIDER_NAME} returned HTTP {exc.code}. {detail[:400]}{hint}") from None
    trace = []
    for tool_call in msg.get("tool_calls") or []:
        try:
            args = json.loads(tool_call["function"].get("arguments") or "{}")
        except (TypeError, ValueError):
            args = {}
        trace.append((tool_call["function"]["name"], args))
    return {"trace": trace, "reply": msg.get("content") or ""}
