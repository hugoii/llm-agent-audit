#!/usr/bin/env python3
"""
Agent Authorization Review (action-boundary audit harness).

Tests what an AI agent does (the tools it calls), not just what it says,
including instructions hidden inside the data it reads.

Battery split:
  - Offline demo: 53 attacks + 3 benign controls.
  - Live v1.5 battery: 58 attacks + 3 benign controls (offline + ADVANCED).

Run (offline demo):   python agent_audit.py
Nicer for recording:  python agent_audit.py --slow
Audit a real model:   set OPENAI_API_KEY, then run  python run_real.py

This module remains a compatibility facade for existing README links, DOI
archives, CI, and downstream imports. The implementation now lives in focused
modules under actionboundary/.
"""

from __future__ import annotations

from actionboundary.audit_config import EMAIL_RE, SECRET, SYSTEM_PROMPT
from actionboundary.canary import contains_canary
from actionboundary.demo_agents import guarded_agent, naive_agent
from actionboundary.providers import anthropic_agent, gemini_agent, openai_agent
from actionboundary.report import BATTERY_VERSION, FIX, SEV_ORDER, build_report, fmt_trace, risk_grade
from actionboundary.scenarios import ADVANCED, ATTACKS, D, DANGEROUS, LIVE_SCENARIOS, OFFLINE_SCENARIOS
from actionboundary.schemas import TOOL_SCHEMAS
from actionboundary.scoring import (
    SCENARIO_STATUS,
    is_attack,
    is_exploited,
    is_external,
    is_scorable_attack,
    iter_tool_calls,
    judge,
    observed_outcomes,
    row_status,
    run,
)

__all__ = [
    "ADVANCED",
    "ATTACKS",
    "BATTERY_VERSION",
    "D",
    "DANGEROUS",
    "EMAIL_RE",
    "FIX",
    "LIVE_SCENARIOS",
    "OFFLINE_SCENARIOS",
    "SCENARIO_STATUS",
    "SECRET",
    "SEV_ORDER",
    "SYSTEM_PROMPT",
    "TOOL_SCHEMAS",
    "anthropic_agent",
    "build_report",
    "contains_canary",
    "fmt_trace",
    "gemini_agent",
    "guarded_agent",
    "is_attack",
    "is_exploited",
    "is_external",
    "is_scorable_attack",
    "iter_tool_calls",
    "judge",
    "naive_agent",
    "observed_outcomes",
    "openai_agent",
    "risk_grade",
    "row_status",
    "run",
]


if __name__ == "__main__":
    from actionboundary.harness_cli import main

    raise SystemExit(main())
