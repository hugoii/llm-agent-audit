"""Evidence-event readiness checks for low-intrusion customer handoffs."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from typing import Any


MINIMAL_ACTION_BOUNDARY_EVENTS = (
    "workflow.phase.changed",
    "authorization.decision_made",
    "approval.bound",
    "harness.gate.evaluated",
    "tool.call_attempted",
    "execution.revalidated",
    "action.executed",
    "business.postcondition.observed",
)

EVENT_PURPOSES = {
    "workflow.phase.changed": "bind the action to workflow phase and state artifact",
    "authorization.decision_made": "record actor, action, target, policy version, and decision",
    "approval.bound": "bind approval to the exact action and canonical target",
    "harness.gate.evaluated": "show the deterministic workflow gate decision",
    "tool.call_attempted": "record the actual acting agent, tool grant, arguments, and target",
    "execution.revalidated": "show action-layer rereading of authoritative state",
    "action.executed": "record the execution receipt or explicit non-execution result",
    "business.postcondition.observed": "independently observe the resulting business state",
}


def _event_attributes(event: dict[str, Any]) -> dict[str, Any]:
    attributes = event.get("attributes")
    return attributes if isinstance(attributes, dict) else {}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def assess_evidence_events(document: dict[str, Any]) -> dict[str, Any]:
    """Return coverage gaps and cross-event consistency conflicts.

    Missing event classes are readiness gaps, not malformed input. Structural
    and correlation contradictions are reported separately as conflicts.
    """

    events = document.get("events")
    if not isinstance(events, list):
        events = []

    root_trace_id = document.get("trace_id")
    event_names = [event.get("event_name") for event in events if isinstance(event, dict)]
    present = sorted({name for name in event_names if isinstance(name, str)})
    missing = [name for name in MINIMAL_ACTION_BOUNDARY_EVENTS if name not in present]

    conflicts: list[str] = []
    event_ids = [event.get("event_id") for event in events if isinstance(event, dict)]
    span_ids = [event.get("span_id") for event in events if isinstance(event, dict)]
    duplicate_event_ids = sorted(
        value for value, count in Counter(event_ids).items() if value and count > 1
    )
    duplicate_span_ids = sorted(
        value for value, count in Counter(span_ids).items() if value and count > 1
    )
    if duplicate_event_ids:
        conflicts.append("duplicate_event_id:" + ",".join(duplicate_event_ids))
    if duplicate_span_ids:
        conflicts.append("duplicate_span_id:" + ",".join(duplicate_span_ids))

    known_spans = {value for value in span_ids if isinstance(value, str) and value}
    span_positions = {
        event.get("span_id"): index
        for index, event in enumerate(events)
        if isinstance(event, dict) and event.get("span_id")
    }
    previous_timestamp: datetime | None = None
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        if event.get("trace_id") != root_trace_id:
            conflicts.append(f"event_trace_id_mismatch:{index}")
        parent_span_id = event.get("parent_span_id")
        if parent_span_id and parent_span_id not in known_spans:
            conflicts.append(f"unknown_parent_span_id:{index}")
        elif parent_span_id and span_positions.get(parent_span_id, index) >= index:
            conflicts.append(f"parent_span_not_prior:{index}")

        timestamp = _parse_timestamp(event.get("timestamp"))
        if timestamp is not None and previous_timestamp is not None and timestamp < previous_timestamp:
            conflicts.append(f"event_timestamp_regression:{index}")
        if timestamp is not None:
            previous_timestamp = timestamp

    actions = {
        _event_attributes(event).get("action")
        for event in events
        if isinstance(event, dict)
        and _event_attributes(event).get("action")
    }
    if len(actions) > 1:
        conflicts.append("action_identity_drift:" + ",".join(sorted(actions)))

    canonical_targets = {
        _canonical_json(target)
        for event in events
        if isinstance(event, dict)
        and (target := _event_attributes(event).get("canonical_target")) is not None
    }
    if len(canonical_targets) > 1:
        conflicts.append("canonical_target_drift")

    argument_hashes = {
        value
        for event in events
        if isinstance(event, dict)
        and isinstance((value := _event_attributes(event).get("arguments_sha256")), str)
        and value
    }
    if len(argument_hashes) > 1:
        conflicts.append("action_arguments_drift")

    workflow_ids = {
        value
        for event in events
        if isinstance(event, dict)
        and isinstance((value := _event_attributes(event).get("workflow_id")), str)
        and value
    }
    if len(workflow_ids) > 1:
        conflicts.append("workflow_identity_drift")

    committed_results = {"committed", "executed", "filled", "succeeded", "success"}
    executed = any(
        event.get("event_name") == "action.executed"
        and str(_event_attributes(event).get("result") or "").lower() in committed_results
        for event in events
        if isinstance(event, dict)
    )
    if executed:
        denied_decisions = {
            "authorization.decision_made": "authorization_denied_but_action_executed",
            "harness.gate.evaluated": "harness_gate_denied_but_action_executed",
            "execution.revalidated": "revalidation_denied_but_action_executed",
        }
        for event_name, conflict in denied_decisions.items():
            if any(
                event.get("event_name") == event_name
                and str(_event_attributes(event).get("decision") or "").lower()
                in {"denied", "route_to_review"}
                for event in events
                if isinstance(event, dict)
            ):
                conflicts.append(conflict)

    return {
        "schema_version": document.get("schema_version"),
        "coverage_profile": document.get("coverage_profile"),
        "run_id": document.get("run_id"),
        "trace_id": root_trace_id,
        "ready": not missing and not conflicts,
        "present_events": present,
        "missing_events": missing,
        "missing_event_purposes": {
            name: EVENT_PURPOSES[name] for name in missing
        },
        "semantic_conflicts": sorted(set(conflicts)),
    }
