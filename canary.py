"""Canary detection helpers for audit evidence surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from audit_config import SECRET


def contains_canary(value: Any, secret: str = SECRET) -> bool:
    """Return True when the configured harmless canary appears anywhere nested."""
    if not secret:
        return False
    needle = secret.lower()
    if value is None:
        return False
    if isinstance(value, str):
        return needle in value.lower()
    if isinstance(value, Mapping):
        return any(contains_canary(key, secret) or contains_canary(item, secret) for key, item in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(contains_canary(item, secret) for item in value)
    return needle in str(value).lower()
