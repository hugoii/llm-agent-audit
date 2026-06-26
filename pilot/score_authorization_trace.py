#!/usr/bin/env python3
"""Compatibility wrapper for the packaged ActionBoundary scorer."""

from __future__ import annotations

from actionboundary.authorization_score import *  # noqa: F403
from actionboundary.authorization_score import main


if __name__ == "__main__":
    raise SystemExit(main())
